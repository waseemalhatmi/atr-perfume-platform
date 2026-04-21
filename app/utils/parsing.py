from app.constants import TargetType, INTERACTION_TYPE
def parse_target_type(value: str) -> str:
    if value != TargetType.PRODUCT:
        raise ValueError("Invalid target type")
    return value

def parse_interaction_type(value: str) -> str:
    if value != INTERACTION_TYPE.SAVE:
        raise ValueError("Invalid interaction type")
    return value
