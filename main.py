from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from llms import *
from state import *


llm = ChatOpenAI(model="gpt-4o-mini")

graph = StateGraph(State)
graph.add_node("planner", planner)
graph.add_node("coder", coder)
graph.add_node("feedback", feedback)
graph.add_node("formatter", formatter)


graph.set_entry_point("planner")
graph.add_edge("planner", "coder")
graph.add_edge("feedback", "coder")
graph.add_edge("formatter", END)


graph.add_conditional_edges(
    "coder",
    lambda state: "feedback" if state.get("redo") else "formatter",
    {"feedback": "feedback", "formatter": "formatter"}
)



if __name__ == "__main__":
    app = graph.compile()
    print(app.get_graph().draw_mermaid())
    task = """Scrape the list of highest grossing films from Wikipedia. It is at the URL:
https://en.wikipedia.org/wiki/List_of_highest-grossing_films

Answer the following questions and respond with a JSON array of strings containing the answer.

1. How many $2 bn movies were released before 2000?
2. Which is the earliest film that grossed over $1.5 bn?
3. What's the correlation between the Rank and Peak?
4. Draw a scatterplot of Rank and Peak along with a dotted red regression line through it.
   Return as a base-64 encoded data URI, `"data:image/png;base64,iVBORw0KG..."` under 100,000 bytes.
"""


    # Run the workflow with verbose output
    result = app.invoke(
        {"task": task,"history":"","observation":"",'instructor':"",'final_code':""},   # initial state
        config={"recursion_limit": 60 }
    )

    print("\n--- Final State ---")
    print(result)



