from example.animations import (
    Add,
    AnimationGroup,
    MoveTo,
    Remove,
    Succession,
    Wait,
)
from manim.mobject.geometry.arc import Circle
from manim.mobject.geometry.polygram import Square, Star
from manim.scene.scene import Scene


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
                    MoveTo(circle, (3, 0, 0)),
                    MoveTo(square, (-3, 0, 0)),
                ),
                Wait(0.5),
                Remove(circle),
                Wait(0.5),
                Add(star),
                Wait(0.5),
                Succession(
                    MoveTo(star, (2, 2, 0)),
                    MoveTo(star, (2, -2, 0)),
                    run_time=2,
                ),
                lag_ratio=1.0,
                run_time=10.0,
            )
        )
