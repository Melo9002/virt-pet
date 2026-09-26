"""Small, UI-independent ASCII animations for the pet."""

from __future__ import annotations

from virtpet.pet import PetCondition, PetState


def pet_art(condition: PetCondition, state: PetState, frame: int,
            paused: bool = False) -> tuple[str, ...]:
    """Return one five-line animation frame for the pet's current mood."""
    phase = 0 if paused else (frame // 5) % 4
    blink = phase == 3

    if state == PetState.SLEEPING:
        dreams = ("       z", "     z Z", "    z  Z", "     Z z")[phase]
        return (dreams, "   /\\_/\\", "  ( -.- )", "   > ^ <", "  /     \\")

    ears = "  /\\_/\\" if phase != 1 else "  /\\_/-"
    tail = ("  /    \\", "  /    \\~", " ~/    \\", "  /    \\~")[phase]

    if condition == PetCondition.HUNGRY:
        eyes = "-.-" if blink else ";o;"
        return ("    .?", ears, f" ( {eyes} )", "   > ~ <", tail)
    if condition == PetCondition.LONELY:
        eyes = "-.-" if blink else "._."
        heart = "      ." if phase % 2 else "      <3"
        return (heart, ears, f" ( {eyes} )", "   > ^ <", tail)
    if condition == PetCondition.DIRTY:
        eyes = "-.-" if blink else ">.<"
        fumes = "  ~    ~" if phase % 2 else "    ~"
        return (fumes, ears, f" ( {eyes} )", "   > # <", tail)
    if condition == PetCondition.SLEEPY:
        eyes = "-.-" if blink or phase % 2 else "u.u"
        return (("      z" if phase % 2 else ""), ears, f" ( {eyes} )",
                "   > ^ <", tail)
    if condition == PetCondition.SICK:
        eyes = "x.x" if blink else "@.@"
        wobble = " *" if phase % 2 else "       *"
        return (wobble, ears, f" ( {eyes} )", "   > ~ <", tail)

    eyes = "-.-" if blink else "^.^"
    sparkle = "       *" if phase == 1 else (" *" if phase == 2 else "")
    return (sparkle, ears, f" ( {eyes} )", "   > ^ <", tail)
