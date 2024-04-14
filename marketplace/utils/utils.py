def revert_dict(d: dict) -> dict:
    # https://stackoverflow.com/questions/483666/reverse-invert-a-dictionary-mapping
    return {v: k for k, v in d.items()}


def remove_empty_keys(d: dict) -> dict:
    return {k: v for k, v in d.items() if v is not None}
