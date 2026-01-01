from fastapi import APIRouter, Depends, HTTPException 
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from app.core.database import get_db
from app.models.pipeline import AnalysisResult, PipelineItem
from app.services.llm_service import llm_service

router = APIRouter()

class ChatRequest(BaseModel):
    query: str
    mode: Optional[str] = "rag" # 'rag' or 'kb-search'

class ChatResponse(BaseModel):
    answer: str
    sources: List[str]
    mode: str

@router.post("/chat", response_model=ChatResponse)
def chat_with_intel(req: ChatRequest, db: Session = Depends(get_db)):
    """
    Dual-Mode Intelligence API:
    1. KB Search (SWG Simulation): Direct Vector Retrieval.
    2. RAG Analysis (W-Intel): LLM Analysis based on Retrieved Data.
    """
    from app.services.vector_service import vector_service
    
    answer = ""
    sources = []
    
    # --- Mode 1: KB Search (Direct Vector) ---
    if req.mode == "kb-search":
        results = []
        
        # 1. Exact Match Lookup (Priority)
        print(f"DEBUG: Lookup exact for {req.query}")
        try:
            exact_match = vector_service.get_item(req.query.strip())
            print(f"DEBUG: Exact match result: {exact_match}")
            if exact_match:
                results.append(exact_match)
        except Exception as e:
            print(f"DEBUG: Exact match ERROR: {e}")
            
        # 2. Semantic Search (Similarity)
        print(f"DEBUG: Sending semantic search for {req.query}")
        try:
            sim_results = vector_service.search(req.query, limit=5)
            print(f"DEBUG: Search result: {len(sim_results)} items")
        except Exception as e:
             print(f"DEBUG: Search ERROR: {e}")
             sim_results = []

        
        # Merge unique
        seen_ids = [r['id'] for r in results]
        for r in sim_results:
            if r['id'] not in seen_ids:
                results.append(r)
        
        if not results:
            answer = "No matching signatures found in Knowledge Base (Vector Store)."
        else:
            answer = "### Knowledge Base Lookup Results (SWG Simulation)\n\n"
            for res in results:
                score = res['score']
                is_exact = (res.get('distance', 1.0) == 0.0) 
                
                # Highlight exact match
                if is_exact:
                    answer += f"🎯 **EXACT MATCH**\n"
                    
                answer += f"**Domain**: {res['fqdn']}\n"
                answer += f"- **Category**: {res['category']}\n"
                answer += f"- **Malicious**: {res['is_malicious']}\n"
                answer += f"- **Similarity Score**: {score:.4f}\n"
                answer += f"- **Snippet**: {res['snippet'][:100]}...\n\n"
                sources.append(res['fqdn'])
                
            answer += "> *Note: This result comes directly from ChromaDB without LLM processing.*"

    # --- Mode 2: RAG Analysis (Default) ---
    else:
        # 1. Retrieve Context (Vector + SQL Fallback)
        context_text = ""
        
        # A. Vector Search
        vector_results = vector_service.search(req.query, limit=5)
        for res in vector_results:
            context_text += f"- [KB Match] Domain: {res['fqdn']}, Category: {res['category']}, Conf: {res['score']:.2f}\n"
            context_text += f"  Summary: {res['snippet']}\n\n"
            sources.append(res['fqdn'])
            
        # B. SQL Search (For items NOT yet in KB, e.g. crawling/discovered)
        # Only needed if we want to show 'pipeline status' for things not yet vectorized
        keywords = [w for w in req.query.split() if len(w) > 3]
        if keywords:
            from sqlalchemy import or_
            from app.models.pipeline import PipelineItem, AnalysisResult
            
            # Find items that match keyword BUT are NOT in the vector sources we just found
            # (To avoid duplication)
            query = db.query(PipelineItem, AnalysisResult).outerjoin(
                AnalysisResult, PipelineItem.id == AnalysisResult.item_id
            )
            filters = [PipelineItem.fqdn.ilike(f"%{k}%") for k in keywords]
            
            sql_results = query.filter(or_(*filters)).limit(5).all()
            
            for item, analysis in sql_results:
                if item.fqdn in sources: 
                    continue # Already found via vector
                    
                context_text += f"- [Pipeline] Domain: {item.fqdn}\n"
                if analysis:
                    context_text += f"  Status: ANALYZED (SQL)\n" # Should be in vector but maybe sync issue
                else:
                    context_text += f"  Status: {item.status}\n"
                    context_text += f"  Note: In pipeline, not yet indexed.\n"
                sources.append(item.fqdn)

        if not context_text:
            context_text = "No intelligence found."

        # 2. LLM Generation
        prompt = f"""
        You are an AI Cyber Intelligence Analyst.
        User Question: "{req.query}"
        
        [Retrieved Intelligence]
        {context_text}
        
        Task:
        - Prioritize Vector KB matches (high confidence).
        - If an item is only in 'Pipeline' status, explain that it is being processed.
        - Synthesize a clear answer suitable for a security analyst.
        - If no info, say so clearly.
        """
        
        try:
            answer = llm_service.simple_chat(prompt)
        except Exception as e:
            answer = f"Error: {e}"

    return {
        "answer": answer,
        "sources": list(set(sources)),
        "mode": req.mode or "rag"
    }
