user_history = {}


def push_history(user_id, data):
    user_history.setdefault(user_id, []).append(data)


def pop_history(user_id):
    stack = user_history.get(user_id, [])
    if stack:
        stack.pop()
    return stack
