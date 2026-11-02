from manim import *

class SimpleBinarySearch(Scene):
    def construct(self):
        self.camera.background_color = WHITE

        ## Introduction screen
        title = Text("Binary Search", color=ORANGE).scale(1.1)

        algo_text = Text(
            "Algorithm:\n"
            "0. If empty, return False\n"
            "1. Find the middle element.\n"
            "2. If it is what we are looking for (key), return True.\n"
            "3a. If our key is smaller than the middle element,\n"
            "    repeat search on the left of the element.\n"
            "3b. Else, repeat search on the right of the element.",
            color=BLACK,
        ).scale(0.4)

        intro_group = VGroup(title, algo_text).arrange(DOWN, buff=0.35).move_to(ORIGIN).shift(UP*0.5)

        self.play(Write(title), Write(algo_text))
        self.wait(3)

        self.play(
            algo_text.animate.to_edge(RIGHT, buff=1.2),
            run_time=1.0,
        )

        ## Show the slicing code
        slicing_code = Code(
            code_string="""
            def binary_search(key, seq):
                if seq == []:
                    return False
                mid = len(seq) // 2
                if key == seq[mid]:
                    return True
                elif key < seq[mid]:
                    return binary_search(key, seq[:mid])
                else:
                    return binary_search(key, seq[mid+1:])
            """,
            add_line_numbers=False
        ).scale(0.55).to_edge(LEFT, buff=1.2)

        self.play(FadeIn(slicing_code))
        slicing_code.save_state()
        highlight_1 = None
        self.wait(3)

        # Move code and text to the corners
        self.play(
            title.animate.to_edge(UP),
            algo_text.animate.to_corner(DL, buff=0.3),
            slicing_code.animate.to_edge(LEFT, buff=0.2).to_edge(UP, buff=1.3),
            run_time=1.0,
        )

        self.wait(0.2)

        ## Simulate a search using an example sequence
        seq = [1, 3, 5, 7, 9, 11, 13]
        key = 9

        array = self.make_array(seq).scale(0.9).move_to(ORIGIN).shift(DOWN * 0.2)
        key_tag = Text(f"key = {key}", color=BLACK).scale(0.55).next_to(array, UP, buff=0.5)

        self.play(FadeIn(array), FadeIn(key_tag))
        self.wait(0.3)

        active = array.copy()
        lo = 0
        hi = len(seq) - 1

        # recursively perform binary search
        while lo <= hi:
            mid = (lo + hi) // 2

            # label the mid
            mid_rect = SurroundingRectangle(array[mid], color=ORANGE, buff=0.12, stroke_width=5)
            mid_label = Text("mid", color=ORANGE).scale(0.45).next_to(array[mid], DOWN, buff=0.25)
            
            # highlight the relevant line of code
            highlight_1 = self.highlight_line(slicing_code, 3, highlight_1)

            self.play(FadeIn(mid_rect), FadeIn(mid_label))
            self.wait(0.3)

            if seq[mid] == key:
                # key is found
                highlight_1 = self.highlight_line(slicing_code, 4, highlight_1)
                equal = Text("key == seq[mid]", color=BLACK, font="Consolas").scale(0.5)
                equal.next_to(array, DOWN, buff=0.6)
                self.play(FadeIn(equal))
                self.wait(0.5)
                
                highlight_1 = self.highlight_line(slicing_code, 5, highlight_1)
                found = Text("Found!", color=GREEN).scale(0.5)
                found.next_to(array, DOWN, buff=1.0)
                self.play(FadeIn(found))
                self.wait(3)

                self.play(
                    FadeOut(found),
                    FadeOut(equal),
                    run_time=0.5,
                )
                break

            if key > seq[mid]:
                # search in right half
                highlight_1 = self.highlight_line(slicing_code, 8, highlight_1)
                eliminated = VGroup(*array[lo : mid + 1])
                kept = VGroup(*array[mid + 1 : hi + 1])
                decision = Text("key > seq[mid] → search in right half", color=BLACK, font="Consolas").scale(0.5)
                self.wait(0.5)
                highlight_1 = self.highlight_line(slicing_code, 9, highlight_1)
                lo = mid + 1
            else:
                # search in left half
                highlight_1 = self.highlight_line(slicing_code, 6, highlight_1)
                eliminated = VGroup(*array[mid : hi + 1])
                kept = VGroup(*array[lo : mid])
                decision = Text("key < seq[mid] → search in left half", color=BLACK, font="Consolas").scale(0.5)
                self.wait(0.5)
                highlight_1 = self.highlight_line(slicing_code, 7, highlight_1)
                hi = mid - 1

            decision.next_to(array, DOWN, buff=0.6)

            self.play(FadeIn(decision))
            self.play(eliminated.animate.set_fill(opacity=0.15), run_time=0.6)
            self.play(kept.animate.scale(1.05), run_time=0.6)
            self.wait(0.3)

            # clean up before next iteration
            self.play(FadeOut(mid_rect), FadeOut(mid_label), FadeOut(decision))
            self.play(kept.animate.scale(1 / 1.05), run_time=0.3)

        # remove the example sequence and related objects
        self.play(
            FadeOut(array),
            FadeOut(key_tag),
            FadeOut(highlight_1),
            FadeOut(mid_rect),
            FadeOut(mid_label),
            run_time=0.5,
        )
        self.wait(0.5)

        # show indexing method (better)
        self.play(slicing_code.animate.restore())

        indexing_text = Text(
            """
            Note: Slicing creates new lists every time!
            An index-based approach keeps the same original list, only moving the low and high pointers.
            Logic remains the same, but saves memory.
            """,
            color=BLACK,
        ).scale(0.35).next_to(title, DOWN, buff=0.5)

        self.play(Write(indexing_text))

        indexing_code = Code(
            code_string="""
            def binary_search(key, low, high):
                if low > high:
                    return False
                mid = (low + high) // 2
                if key == seq[mid]:
                    return True
                elif key < seq[mid]:
                    return binary_search(key, low, mid - 1)
                else:
                    return binary_search(key, mid + 1, high)
            """,
            add_line_numbers=False
        ).scale(0.55).to_edge(RIGHT, buff=1.2)

        self.play(FadeIn(indexing_code))

        self.wait(1)

        # highlight the changes
        highlight_2, highlight_3, highlight_4, highlight_5 = None, None, None, None

        highlight_2 = self.highlight_line(slicing_code, 7, highlight_2, color=RED)
        highlight_4 = self.highlight_line(indexing_code, 7, highlight_4, color=GREEN)
        highlight_3 = self.highlight_line(slicing_code, 9, highlight_3, color=RED)
        highlight_5 = self.highlight_line(indexing_code, 9, highlight_5, color=GREEN)

        self.wait(2)

        self.play(
            FadeOut(highlight_2),
            FadeOut(highlight_3),
            FadeOut(highlight_4),
            FadeOut(highlight_5),
            FadeOut(slicing_code),
            run_time=0.5,
        )
        
        # leave the index-based version
        self.play(indexing_code.animate.move_to(ORIGIN))

        self.wait(2)

    # ---------- helpers ----------

    def make_array(self, seq):
        cells = []
        for n in seq:
            box = RoundedRectangle(width=1.0, height=0.8, corner_radius=0.15, stroke_width=2)
            txt = Text(str(n), color=BLACK).scale(0.55)
            txt.move_to(box.get_center())
            cells.append(VGroup(box, txt))
        return VGroup(*cells).arrange(RIGHT, buff=0.15)
    
    def highlight_line(self, code, line_idx, current=None, color=YELLOW):
        rect = SurroundingRectangle(
            code.code_lines[line_idx],
            buff=0.12,
            color=color,
        ).set_fill(color, opacity=0.1)

        if current is None:
            self.play(FadeIn(rect))
            return rect
        else:
            self.play(Transform(current, rect))
            return current

