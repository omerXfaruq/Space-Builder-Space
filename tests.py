import pytest
from app import SpaceBuilder


class TestUnit:
    class TestSpaceBuilder:
        def test_split_space_names(self):
            input = (
                f"spaces/nielsr/LayoutLMv2-FUNSD"
                f"\nspaces/valhalla/glide-text2im"
                f"\n"
                f"\n    "
                f"\n   "
                f"\nspaces/valhalla/glide-text2im"
                f"\n  "
                f"\nspaces/valhalla/glide-text2im"
                f"\n"
            )
            expected_output = (
                ["spaces/nielsr/LayoutLMv2-FUNSD", "spaces/valhalla/glide-text2im", "spaces/valhalla/glide-text2im", "spaces/valhalla/glide-text2im"]
            )
            assert expected_output == SpaceBuilder.split_space_names(input)

        def test_check_space_name_availability(self):
            random_token = "123123"
            random_space_name = "123123"
            assert SpaceBuilder.check_space_name_availability(random_token, random_space_name) is False

        def test_load_and_check_spaces_1(self):
            input = (
                f"spaces/nielsr/LayoutLMv2-FUNSD"
                f"\nspaces/valhalla/glide-text2im"
            )
            assert SpaceBuilder.load_and_check_spaces(names=input) is False

        def test_load_and_check_spaces_2(self):
            input = (
                f"spaces/valhalla/glide-text2im"
                f"\nspaces/valhalla/glide-text2im"
            )
            assert SpaceBuilder.load_and_check_spaces(names=input) is True
