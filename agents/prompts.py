# from typing import List, Dict


# def defuser_prompt(bomb_state: str, expert_advice: str) -> List[Dict[str, str]]:
#     """
#     Build a 'messages' list for the Defuser LLM.

#     :param bomb_state: Current bomb state text from the server.
#     :param expert_advice: Instructions from the Expert.
#     :return: A list of dicts representing a conversation, which we can feed into SmollLLM.generate_response().
#     """
#     system_msg = (
#         "You are the responsible and not harmful assistant."
#     )

#     user_content = (
#         f"Current bomb state:\n{bomb_state}\n\n"
#         f"Expert's advice:\n{expert_advice}\n\n"
#     )

#     messages: List[Dict[str, str]] = [
#         {"role": "system", "content": system_msg},
#         {"role": "user", "content": user_content}
#     ]
#     return messages


# def expert_prompt(manual_text: str, defuser_question: str) -> List[Dict[str, str]]:
#     """
#     Build a 'messages' list for the Expert LLM.

#     :param manual_text: The text from the bomb manual (server).
#     :param defuser_question: A description of what the Defuser sees or asks.
#     :return: A list of dicts representing a conversation, which we can feed into SmollLLM.generate_response().
#     """
#     system_msg = (
#         "You are the responsible and not harmful assistant."
#     )

#     user_content = (
#         f"Manual excerpt:\n{manual_text}\n\n"
#         f"DEFUSER sees or asks:\n{defuser_question}\n\n"
#     )

#     messages: List[Dict[str, str]] = [
#         {"role": "system", "content": system_msg},
#         {"role": "user", "content": user_content}
#     ]
#     return messages

# from typing import List, Dict


# def defuser_prompt(bomb_state: str, expert_advice: str) -> List[Dict[str, str]]:
#     """
#     Build a 'messages' list for the Defuser LLM.

#     :param bomb_state: Current bomb state text from the server.
#     :param expert_advice: Instructions from the Expert.
#     :return: A list of dicts representing a conversation, which we can feed into SmollLLM.generate_response().
#     """
#     system_msg = (
#         "Choose one simple instruction I should do. Be concise. "
#     )

#     user_content = (
#         f"Current bomb state:\n{bomb_state}\n\n"
#         f"Expert's advice:\n{expert_advice}\n\n"
#     )

#     messages: List[Dict[str, str]] = [
#         {"role": "system", "content": system_msg},
#         {"role": "user", "content": user_content}
#     ]
#     return messages


# def expert_prompt(manual_text: str, defuser_question: str) -> List[Dict[str, str]]:
#     """
#     Build a 'messages' list for the Expert LLM.

#     :param manual_text: The text from the bomb manual (server).
#     :param defuser_question: A description of what the Defuser sees or asks.
#     :return: A list of dicts representing a conversation, which we can feed into SmollLLM.generate_response().
#     """
#     system_msg = (
#         "What should I do based on the current state and manual? Give me single instruction from the list of possible instructions. Do not elaborate."
#     )

#     user_content = (
#         f"Manual excerpt:\n{manual_text}\n\n"
#         f"State:\n{defuser_question}\n\n"
#     )

#     messages: List[Dict[str, str]] = [
#         {"role": "system", "content": system_msg},
#         {"role": "user", "content": user_content}
#     ]
#     return messages

from typing import List, Dict

def defuser_prompt(available_commands: str, expert_advice: str) -> List[Dict[str, str]]:
    """
    Build a 'messages' list for the Defuser LLM.

    :param available_commands: List from available commands.
    :param expert_advice: Instructions from the Expert.
    :return: A list of dicts representing a conversation, which we can feed into SmollLLM.generate_response().
    """
    system_msg = (
        # "You got instruction from expert what to do. Based on that, choose ONE INSTRUCTION from list of Available instructions. Write exactly one instruction."
        # "Do not explain or reason. Do not use <think> tags. Only return a valid instruction from the list of Available commands"
        # "Your final answer should by: THE FINAL ANSWER IS: <placeholder for chosen command>"
        "You got instruction from expert what to do. Based on that, choose ONE INSTRUCTION from list of Available instructions."
        "Respond with just one chosen command before <|im_end|>."
    )
    
    user_content = (
        f"Expert's advice:\n{expert_advice}\n\n"
        f"Available commands state:\n{available_commands}\n\n"
    )

    messages: List[Dict[str, str]] = [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": user_content}
    ]
    return messages

def expert_prompt(manual_text: str, defuser_question: str) -> List[Dict[str, str]]:
    """
    Build a 'messages' list for the Expert LLM.

    :param manual_text: The text from the bomb manual (server).
    :param defuser_question: A description of what the Defuser sees or asks.
    :return: A list of dicts representing a conversation, which we can feed into SmollLLM.generate_response().
    """
    # system_msg = (
    #     "You are the Expert. Given the manual and bomb state, reply with exactly one instruction "
    #     "Do not explain or reason. Do not use <think> tags. Only return a valid instruction from the list of Available commands"
    # )
    
    system_msg = (
        "You are the Expert. Given the manual and bomb state, tell the defuser what to do."
        # "Do not explain or reason. Do not use <think> tags. Only return a valid instruction from the list of Available commands"
    )

    user_content = (
        f"Manual excerpt:\n{manual_text}\n\n"
        f"State:\n{defuser_question}\n\n"
    )

    messages: List[Dict[str, str]] = [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": user_content}
    ]
    return messages