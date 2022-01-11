from typing import List

import numpy as np
import requests
import gradio as gr
import time

from huggingface_hub import (
    create_repo,
    get_full_repo_name,
    upload_file,
)


class SpaceBuilder:
    error_message = None
    url = None

    @classmethod
    def split_space_names(cls, names: str) -> List[str]:
        """
        Splits and filters the given space_names.

        :param names: space names
        :return: Name List
        """
        name_list = names.split("\n")
        filtered_list = []
        for name in name_list:
            if not (name == "" or name.isspace()):
                filtered_list.append(name)
        return filtered_list

    @classmethod
    def file_as_a_string(cls, name_list: List[str], title: str, description: str) -> str:
        """
        Returns the file that is going to be created in the new space as string.

        :param name_list: list of space names
        :param title: title
        :param description: description
        :return: file as a string
        """
        return (
            f"import gradio as gr"
            f"\nname_list = {name_list}"
            f"\ninterfaces = [gr.Interface.load(name) for name in name_list]"
            f"\ngr.mix.Parallel(*interfaces, title=\"{title}\", description=\"{description}\").launch()"
        )

    @classmethod
    def control_input_and_output_types(
        cls, interface_list: List["gr.Interface"]
    ) -> bool:
        """
        Controls whether if input and output types of the given interfaces are the same.

        :param interface_list: list of interfaces
        :return: True if all input and output types are the same
        """
        first_input_types = [
            type(input) for input in interface_list[0].input_components
        ]
        first_output_types = [
            type(output) for output in interface_list[0].output_components
        ]
        for interface in interface_list:
            interface_input_types = [
                type(input) for input in interface.input_components
            ]
            if not np.all(
                interface_input_types == first_input_types
            ):  # Vectorize the comparison and don't use double for loop
                cls.error_message = "Provided space input types are different"
                return False
            interface_output_types = [
                type(output) for output in interface.output_components
            ]
            if not np.all(interface_output_types == first_output_types):
                cls.error_message = "Provided space output types are different"
                return False

        return True

    @classmethod
    def check_space_name_availability(cls, hf_token: str, space_name: str) -> bool:
        """
        Check whether if the space_name is currently used.

        :param hf_token: hugging_face token
        :param space_name:
        :return: True if the space_name is available
        """
        try:
            repo_name = get_full_repo_name(model_id=space_name, token=hf_token)
        except Exception as ex:
            print(ex)
            cls.error_message = "You have given an incorrect HuggingFace token"
            return False
        try:
            url = f"https://huggingface.co/spaces/{repo_name}"
            response = requests.get(url)
            if response.status_code == 200:
                cls.error_message = f"The {repo_name} is already used."
                return False
            else:
                print(f"The space name {repo_name} is available")
                return True
        except Exception as ex:
            print(ex)
            cls.error_message = "Can not send a request to https://huggingface.co"
            return False

    @classmethod
    def load_and_check_spaces(cls, names: str) -> bool:
        """
        Loads given space inputs as interfaces and checks whether if they are loadable.

        :param names: Input space names
        :return: True if check is successful
        """
        name_list = cls.split_space_names(names)

        try:
            # We could gather these interfaces in parallel if gradio was supporting async gathering. It will probably be possible after the migration to the FastAPI is completed.
            interfaces = [gr.Interface.load(name) for name in name_list]
        except Exception as ex:
            print(ex)
            cls.error_message = (
                f"One of the given space cannot be loaded to gradio, sorry for the inconvenience. "
                f"\nPlease use different input space names!"
            )
            return False
        if not cls.control_input_and_output_types(interfaces):
            return False
        else:
            print("Loaded and checked input spaces, great it works!")
            return True

    @classmethod
    def create_space(cls, input_space_names: str, target_space_name: str, hf_token: str, title: str, description: str) -> bool:
        """
        Creates the target space with the given space names.

        :param input_space_names: Input space name_list
        :param target_space_name: Target space_name
        :param hf_token: HuggingFace Write Token
        :param title: Target Interface Title
        :param description: Target Interface Description
        :return: True if success
        """
        name_list = cls.split_space_names(input_space_names)
        try:
            create_repo(name=target_space_name, token=hf_token, repo_type="space", space_sdk="gradio")
        except Exception as ex:
            print(ex)
            cls.error_message = "Please provide a correct space name as Only regular characters and '-', '_', '.' accepted. '--' and '..' are forbidden. '-' and '.' cannot start or end the name."
            return False
        repo_name = get_full_repo_name(model_id=target_space_name, token=hf_token)

        try:
            file_string = cls.file_as_a_string(name_list, title, description)
            temp_file = open("temp_file.txt", "w")
            temp_file.write(file_string)
            temp_file.close()
        except Exception as ex:
            print(ex)
            cls.error_message = "An exception occurred during temporary file writing"
            return False

        # Sleep a little bit otherwise the interface might not build at the space after uploading a file
        time.sleep(1)
        try:
            file_url = upload_file(
                path_or_fileobj="temp_file.txt",
                path_in_repo="app.py",
                repo_id=repo_name,
                repo_type="space",
                token=hf_token,
            )
            cls.url = f"https://huggingface.co/spaces/{repo_name}"
            return True
        except Exception as ex:
            print(ex)
            cls.error_message = (
                "An exception occurred during writing app.py to the target space"
            )
            return False

    @staticmethod
    def build_space(
        space_names: str, hf_token: str, target_space_name: str, interface_title: str, interface_description: str
    ) -> str:
        """
        Creates a space with given input spaces.

        :param space_names: Multiple space names split with new lines
        :param hf_token: HuggingFace token
        :param target_space_name: Target Space Name
        :param interface_title: Target Interface Title
        :param interface_description: Target Interface Description
        :return:
        """
        if (
            space_names == "" or space_names.isspace()
            or hf_token == "" or hf_token.isspace()
            or target_space_name == "" or target_space_name.isspace()
            or interface_title == "" or interface_title.isspace()
            or interface_description == "" or interface_description.isspace()
        ):
            return "Please fill all the inputs"
        if not SpaceBuilder.check_space_name_availability(hf_token=hf_token, space_name=target_space_name):
            return SpaceBuilder.error_message
        if not SpaceBuilder.load_and_check_spaces(names=space_names):
            return SpaceBuilder.error_message
        if not SpaceBuilder.create_space(input_space_names=space_names, target_space_name=target_space_name, hf_token=hf_token, title=interface_title, description=interface_description):
            return SpaceBuilder.error_message

        return SpaceBuilder.url


if __name__ == "__main__":
    iface = gr.Interface(
        fn=SpaceBuilder.build_space,
        inputs=[
            gr.inputs.Textbox(
                lines=4,
                placeholder=(
                    f"Drop model and space links at each line and I will create a new space comparing them. Usage examples:"
                    f"\nspaces/deepklarity/poster2plot"
                    f"\nmodels/gpt2"
                ),
            ),
            gr.inputs.Textbox(lines=1, placeholder="HuggingFace Write Token"),
            gr.inputs.Textbox(lines=1, placeholder="Name for the target space, ie. space-building-space"),
            gr.inputs.Textbox(lines=1, placeholder="Title for the target space interface, ie. Title"),
            gr.inputs.Textbox(lines=1, placeholder="Description for the target space interface, ie. Description"),
        ],
        title="Space that builds another Space",
        description="I can create another space which will compare the models or spaces you provide to me",
        outputs="text",
    )
    iface.launch()
