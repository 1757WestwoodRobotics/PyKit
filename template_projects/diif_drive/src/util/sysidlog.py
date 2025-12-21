from wpilib.sysid import State


def sysIdStateToStr(state: State) -> str:
    stateMap = {
        State.kQuasistaticForward: "quasistatic-forward",
        State.kQuasistaticReverse: "quasistatic-reverse",
        State.kDynamicForward: "dynamic-forward",
        State.kDynamicReverse: "dynamic-reverse",
        State.kNone: "none",
    }
    return stateMap.get(state, "none")
