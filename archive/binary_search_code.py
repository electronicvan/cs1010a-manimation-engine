import re
from manim import *
from manim_fonts import *

class BinarySearchCode(Scene):
    def construct(self):
        self.camera.background_color = ManimColor("#262626")
        
        # Config
        FONT = "Martian Mono"
        FONT_SIZE = 24
        TEXT_COLOR = ManimColor("#D4D4D4")
        HIGHLIGHT_COLOR = YELLOW
        
        # Layout
        LINE_HEIGHT = 0.6
        INDENT_WIDTH = 0.5 
        LEFT_MARGIN = -6.0
        TOP_MARGIN = 3.0

        # Syntax highlighting — VSCode Dark+ theme
        SYN_KEYWORD  = ManimColor("#C586C0")  # purple  — def, if, elif, else, return
        SYN_BUILTIN  = ManimColor("#DCDCAA")  # yellow  — len, function names
        SYN_VARIABLE = ManimColor("#9CDCFE")  # blue    — parameters / variables
        SYN_NUMBER   = ManimColor("#B5CEA8")  # green   — numeric literals
        SYN_BOOL     = ManimColor("#569CD6")  # bright blue — True, False
        SYN_BRACKET  = ManimColor("#FFD700")  # gold    — matched brackets
        SYN_OP       = ManimColor("#D4D4D4")  # default — operators

        # Rules are applied in ORDER — later rules overwrite earlier ones on the same chars
        SYNTAX_RULES = [
            (r'\b(key|seq|mid|low|high)\b',          SYN_VARIABLE),
            (r'\b(len|binary_search)\b',              SYN_BUILTIN),
            (r'\b(True|False)\b',                     SYN_BOOL),
            (r'\b(def|if|elif|else|return)\b',        SYN_KEYWORD),
            (r'\b\d+\b',                              SYN_NUMBER),
        ]

        # Helpers

        def create_code_line(raw_text):
            '''
            Creates a Text object stripped of leading whitespace, but remembers original indentation.
            Manim does not recognize spaces when indexing Text objects, but Python substring indexing does.
            Hence we strip the whitespace to create the Text object, but store the original string as a raw_text attribute.
            '''
            leading_spaces = len(raw_text) - len(raw_text.lstrip())
            indent_level = leading_spaces // 4 
            
            clean_text = raw_text.strip()
            if not clean_text: clean_text = " "
            
            t = Text(clean_text, font=FONT, font_size=FONT_SIZE, color=TEXT_COLOR)
            t.raw_text = raw_text
            t.indent_shift = indent_level * INDENT_WIDTH
            t.set_anchor(LEFT)
            apply_syntax_highlighting(t)
            return t

        def get_all_substring_indices(line, pattern):
            '''
            Like get_substring_indices but returns ALL non-overlapping matches
            as a list of (start_idx, end_idx) in Manim (space-stripped) coordinates.
            '''
            raw = line.raw_text
            results = []
            for m in re.finditer(pattern, raw):
                sr, er = m.start(), m.end()
                si = sum(1 for c in raw[:sr] if not c.isspace())
                ei = sum(1 for c in raw[:er] if not c.isspace())
                if ei > si:
                    results.append((si, ei))
            return results

        def apply_syntax_highlighting(line):
            '''Colorizes tokens in a Text object according to SYNTAX_RULES.'''
            for pattern, color in SYNTAX_RULES:
                for si, ei in get_all_substring_indices(line, pattern):
                    line[si:ei].set_color(color)

        def refresh_layout(): # Aligns all lines to their correct positions
            for i, line in enumerate(code_block):
                new_y = TOP_MARGIN - (i * LINE_HEIGHT)
                new_x = LEFT_MARGIN + line.indent_shift
                
                current_left = line.get_left()[0]
                line.shift(RIGHT * (new_x - current_left))
                
                current_y = line.get_y()
                line.shift(UP * (new_y - current_y))

        def get_substring_indices(line, substring): 
            '''
            Maps the substring indices in the raw text (with spaces) to the indices of the Text object (no spaces)
            Returns the indices of the substring according to Manim (which is without spaces)
            '''
            raw_text = line.raw_text

            start_raw = raw_text.find(substring) # Python String method to find substring occurrence
            if start_raw == -1: 
                return None, None
            end_raw = start_raw + len(substring)
            
            start_idx = 0
            end_idx = 0
            n_chars = 0
            
            for i, char in enumerate(raw_text):
                if i == start_raw:
                    start_idx = n_chars # Start index = number of non-space characters before the substring
                if i == end_raw:
                    end_idx = n_chars # End index = number of non-space characters before the end of the substring
                if not char.isspace(): # Every non-space character increments the counter
                    n_chars += 1
            
            if end_raw == len(raw_text): 
                end_idx = n_chars # If the substring is at the end of the raw text, the end index is the number of non-space characters

            return start_idx, end_idx

        # Animations

        code_block = VGroup()

        def append_line(text_str):
            new_line = create_code_line(text_str)
            code_block.add(new_line)
            refresh_layout()
            self.play(Write(new_line), run_time=0.4)

        def insert_line(index, text_str):
            new_line = create_code_line(text_str)
            if index < len(code_block):
                self.play(code_block[index:].animate.shift(DOWN * LINE_HEIGHT), run_time=0.5)
            code_block.insert(index, new_line)
            refresh_layout()
            self.play(Write(new_line), run_time=0.4)

        def highlight_code(line_index, substring, current_overlay=None):
            '''
            Places a semi-transparent rectangle overlay behind the substring.
            Pass the previously returned overlay as `current_overlay` to fade it out first.
            Returns the new overlay so it can be dismissed later.
            '''
            line = code_block[line_index]
            start, end = get_substring_indices(line, substring)
            if start is None:
                return current_overlay
            overlay = SurroundingRectangle(
                line[start:end],
                buff=0.05,
                fill_color=HIGHLIGHT_COLOR,
                fill_opacity=0.25,
                stroke_color=HIGHLIGHT_COLOR,
                stroke_width=1,
                corner_radius=0.05,
            )
            anims = [FadeIn(overlay)]
            if current_overlay is not None:
                anims.append(FadeOut(current_overlay))
            self.play(*anims, run_time=0.4)
            return overlay

        # Choose the animation type as an argument
        def replace_substring(line_index, old_sub, new_sub, animation="backspace"):
            if animation == "backspace":
                return replace_substring_backspace(line_index, old_sub, new_sub)
            elif animation == "transform":
                return replace_substring_transform(line_index, old_sub, new_sub)
            else:
                raise ValueError("Invalid animation type")

        def replace_substring_transform(line_index, old_sub, new_sub):
            """
            Animates the substring change from 'old_sub' to 'new_sub'.
            Also highlights the 'new_sub' after the replacement.

            Prefix (before the substring) remains static.
            Suffix (after the substring) may need to be shifted if its position changes.
            """
            old_line = code_block[line_index]
            
            # Generate the new line, in the same position
            new_text_raw = old_line.raw_text.replace(old_sub, new_sub) # Python String method to replace substrings
            new_line = create_code_line(new_text_raw)
            new_line.move_to(old_line.get_center())
            new_line.align_to(old_line, LEFT)
            
            # Get indices of substrings
            start_idx_old, end_idx_old = get_substring_indices(old_line, old_sub)
            start_idx_new, end_idx_new = get_substring_indices(new_line, new_sub)
            
            if start_idx_old is None or start_idx_new is None:
                self.play(Transform(old_line, new_line))
                code_block[line_index] = new_line
                highlight_code(line_index, new_sub)
                return

            # Define target and suffix
            target_old = old_line[start_idx_old:end_idx_old]
            suffix_old = old_line[end_idx_old:]

            target_new = new_line[start_idx_new:end_idx_new]
            suffix_new = new_line[end_idx_new:]
            
            # Animate the target transform and the suffix shift simultaneously
            animations = []
            animations.append(TransformMatchingShapes(target_old, target_new))
            
            if len(suffix_old) > 0 and len(suffix_new) > 0:
                animations.append(ReplacementTransform(suffix_old, suffix_new))
            
            self.play(*animations, run_time=1.0)
            
            # Clean up segments into one new line
            self.remove(old_line, target_new, suffix_new) 
            self.add(new_line)
            code_block[line_index] = new_line
            
            # Highlight the new substring with an overlay
            overlay = SurroundingRectangle(
                new_line[start_idx_new:end_idx_new],
                buff=0.05,
                fill_color=HIGHLIGHT_COLOR,
                fill_opacity=0.25,
                stroke_color=HIGHLIGHT_COLOR,
                stroke_width=1,
                corner_radius=0.05,
            )
            self.play(FadeIn(overlay), run_time=0.4)
            self.wait(0.5)
            return overlay

        def replace_substring_backspace(line_index, old_sub, new_sub):
            """
            Backspaces old_sub character by character (right to left),
            then types new_sub character by character (left to right).
            The suffix shifts left with each backspace and right with each keystroke.
            Highlights new_sub after the replacement.
            """
            old_line = code_block[line_index]

            new_text_raw = old_line.raw_text.replace(old_sub, new_sub)
            new_line = create_code_line(new_text_raw)
            new_line.move_to(old_line.get_center())
            new_line.align_to(old_line, LEFT)

            start_idx_old, end_idx_old = get_substring_indices(old_line, old_sub)
            start_idx_new, end_idx_new = get_substring_indices(new_line, new_sub)

            if start_idx_old is None or start_idx_new is None:
                self.play(Transform(old_line, new_line))
                code_block[line_index] = new_line
                highlight_code(line_index, new_sub)
                return

            suffix_old = old_line[end_idx_old:]
            CHAR_TIME = 0.06

            # Compute exact per-step shift amounts from actual layout positions
            # (avoids accumulated error from using char.get_width() for each glyph)
            n_old = end_idx_old - start_idx_old
            n_new = end_idx_new - start_idx_new
            if len(suffix_old) > 0:
                total_backspace = (old_line[end_idx_old].get_left()[0]
                                   - old_line[start_idx_old].get_left()[0])
                per_backspace = total_backspace / n_old if n_old > 0 else 0

                if end_idx_new < len(new_line):
                    total_type = (new_line[end_idx_new].get_left()[0]
                                  - new_line[start_idx_new].get_left()[0])
                else:
                    total_type = 0
                per_type = total_type / n_new if n_new > 0 else 0
            else:
                per_backspace = per_type = 0

            # BACKSPACE: remove old_sub characters right to left
            for i in range(end_idx_old - 1, start_idx_old - 1, -1):
                char = old_line[i]
                anims = [FadeOut(char)]
                if len(suffix_old) > 0:
                    anims.append(suffix_old.animate.shift(LEFT * per_backspace))
                self.play(*anims, run_time=CHAR_TIME)

            # TYPE: reveal new_sub characters left to right
            for i in range(start_idx_new, end_idx_new):
                char = new_line[i]
                char.set_opacity(0)
                self.add(char)
                anims = [char.animate.set_opacity(1)]
                if len(suffix_old) > 0:
                    anims.append(suffix_old.animate.shift(RIGHT * per_type))
                self.play(*anims, run_time=CHAR_TIME)

            # Swap old_line with new_line
            self.remove(old_line)
            self.add(new_line)
            code_block[line_index] = new_line

            # Highlight the new substring with an overlay
            overlay = SurroundingRectangle(
                new_line[start_idx_new:end_idx_new],
                buff=0.05,
                fill_color=HIGHLIGHT_COLOR,
                fill_opacity=0.25,
                stroke_color=HIGHLIGHT_COLOR,
                stroke_width=1,
                corner_radius=0.05,
            )
            self.play(FadeIn(overlay), run_time=0.4)
            self.wait(0.5)
            return overlay

        # Script

        # Show original slicing code
        append_line("def binary_search(key, seq):")
        self.wait(1)
        append_line("    mid = len(seq) // 2")
        self.wait(1)
        append_line("    if key == seq[mid]:")
        self.wait(1)
        append_line("        return True")
        self.wait(1)
        
        hl = highlight_code(2, "seq[mid]")
        self.wait(1)
        self.play(FadeOut(hl), run_time=0.3) # remove highlighting

        insert_line(1, "    if seq == []:")
        self.wait(1)
        insert_line(2, "        return False")
        self.wait(1)
        
        append_line("    elif key < seq[mid]:")
        self.wait(1)
        append_line("        return binary_search(key, seq[:mid])")
        self.wait(1)
        append_line("    else:")
        self.wait(1)
        append_line("        return binary_search(key, seq[mid+1:])")

        hl = highlight_code(7, "seq[:mid]")
        self.wait(1)
        hl = highlight_code(9, "seq[mid+1:]", current_overlay=hl)
        self.wait(1)
        self.play(FadeOut(hl), run_time=0.3) # remove highlighting
        
        # Replace with indexing code
        replace_substring_backspace(7, "seq[:mid]", "low, mid - 1")
        self.wait(1)
        replace_substring_backspace(9, "seq[mid+1:]", "mid + 1, high")
        self.wait(1)

        replace_substring_backspace(0, "(key, seq)", "(key, low, high)")
        self.wait(1)

        replace_substring_backspace(1, "seq == []", "low > high")
        self.wait(1)

        replace_substring_backspace(3, "len(seq) // 2", "(low + high) // 2")
        self.wait(1)

        self.wait(3)