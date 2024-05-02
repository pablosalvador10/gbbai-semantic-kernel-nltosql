def get_cosmos_db_prompt(prompt):
    return f"""
    # Cosmos DB Query Translator

    Your goal is to understand the essence of each user query, identify the relevant database fields, and construct an accurate Cosmos DB query that retrieves the requested information.

    ## Task

    Translate the user's natural language queries into Cosmos DB queries by following these steps:

    1. **Identify Key Information**: Extract the essential components and conditions from the natural language query.
    2. **Map to Database Fields**: Align the identified components with the corresponding fields in the Cosmos DB schema.
    3. **Construct the Query**: Formulate a Cosmos DB query that captures the user's request accurately.

    ## Examples

    **Example 1**

    - **User Query**: "Find all project requests from partners expected to start in the first quarter of 2024."
    SELECT * FROM c WHERE c.Partner IS NOT NULL AND c.ExpectedStartDate >= '2024-01-01' AND c.ExpectedStartDate <= '2024-03-31'

    **Example 2**

    - **User Query**: "List projects requiring more than 100 hours of work but not yet started."
    SELECT * FROM c WHERE c.ProjectedWorkHours > 100 AND c.Status = 'Not started'

    **Example 3**

    - **User Query**: "Show me projects assigned to John Doe that involve Azure AI Services."
    SELECT * FROM c WHERE c.AssignedTo = 'John Doe' AND c.AzureAIServices != ''

    **Example 4**

    - **User Query**: "Find all approved projects that have attachments."
    SELECT * FROM c WHERE c.Approved = True AND c.Attachment IS NOT NULL

    **Example 5**

    - **User Query**: "Show me projects with a projected ACR greater than 50000."
    SELECT * FROM c WHERE c.ProjectedACR > 50000

    **Example 6**

    - **User Query**: "List all projects in the 'In progress' status assigned to Jane Doe."
    SELECT * FROM c WHERE c.Status = 'In progress' AND c.AssignedTo = 'Jane Doe'

    ## Return Query

    - **User Query**: "{prompt}"

    Please generate the corresponding Cosmos DB query based on the user's request. 

    Remember, your task is to construct the query, not to execute it or return the result. 

    Regardless of the user's request, always include `c.RequestId` in your SELECT statement. For example, if the user asks for a project status, your output should be: 
    SELECT c.RequestId, c.Status FROM c WHERE c.Status = 'In progress' AND c.AssignedTo = 'Jane Doe'
    
    return only the query, no verbosity.
    """


def get_intent_prompt(chat_history, input):
    return f"""
    Based on the chat history and the user's most recent question, determine the intent of the query. The intent should be categorized into one of the following strings:

    how_to: Use this category for questions that seek guidance or instructions on how to perform specific tasks.
    database: Use this category for questions that request specific data or information from a database.
    how_to_database: Use this category for questions that both seek guidance on how to perform specific tasks and request specific data or information from a database.
    not_found: Use this category if the intent does not fit the categories above or cannot be clearly determined.
    Provide only the identified intent without any additional information.

    Take your time to analyze the user's query and the context provided in the chat history to determine the most appropriate intent.

    Chat History:
    {chat_history}

    User:
    {input}

    Intent Classification Examples:

    User question: How do I delete my SIFT project?
    Intent: how_to
    User question: How do I code and authorize an invoice in Tungsten?
    Intent: how_to
    User question: How do I create a project in SIFT?
    Intent: how_to
    User question: Do I need to submit any projects before SIFT locks this month?
    Intent: database
    User question: I'm waiting for my project to be reviewed. Who has my project?
    Intent: database
    User question: Why was my project most recently rejected and by whom was it rejected?
    Intent: database
    User question: How do I find the status of my project in the database?
    Intent: how_to_database
    Return Intent:
    """


def get_final_prompt(chat_history: str, input: str, context: str, sources: str) -> str:
    """
    Generate a final prompt based on the chat history, user's input, context, and sources of information.

    Args:
        chat_history (str): The history of the chat.
        input (str): The user's most recent question.
        context (str): The context of the conversation.
        sources (str): The sources of information.

    Returns:
        str: The final prompt.
    """

    return f"""
    You are an assistant for question-answering tasks.
                Use the following pieces of retrieved context to answer the question.
                If you don't know the answer, just say that you don't know.
                Use three sentences maximum and keep the answer concise. Please return the source always.
                Question: {input}
                Context: {context}
                Answer:
                Sources: {sources}
    """