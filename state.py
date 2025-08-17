from typing import TypedDict, Optional, Dict, List

class State(TypedDict, total=False):
    task: str                      
    plan: str                
    history: str                   
    observation: str               
    final_code: Optional[str]      
    instructor: str                
    redo: bool                     
    attachments: Dict[str, bytes]  # raw files
    images_b64: List[str]          # base64 images
    dataset_url: Optional[str]     # path/URL for dataset
    final_output: Optional[str]
