from manim.mobject.geometry.arc import Circle
from manim.mobject.geometry.polygram import Square, Star
from manim.scene.scene import Scene

from .animations import (
    Add,
    AnimationGroup,
    MoveToAnimation,
    Remove,
    Succession,
    Wait,
)


class ExampleScene(Scene):
    def construct(self) -> None:
        circle, square, star = Circle(), Square(), Star()
        self.play(
            AnimationGroup(
                Wait(0.5),
                Add(circle),
                Wait(0.5),
                Add(square),
                Wait(0.5),
                AnimationGroup(
                    MoveToAnimation(circle, (3, 0, 0)),
                    MoveToAnimation(square, (-3, 0, 0)),
                ),
                Wait(0.5),
                Remove(circle),
                Wait(0.5),
                Add(star),
                Wait(0.5),
                Succession(
                    MoveToAnimation(star, (2, 2, 0)),
                    MoveToAnimation(star, (2, -2, 0)),
                    run_time=2,
                ),
                lag_ratio=1.0,
                run_time=10.0,
            )
        )
