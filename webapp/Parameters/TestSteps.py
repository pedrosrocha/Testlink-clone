
from .Database.steps_database import DatabaseConnector
from ..utils.return_data_model import DatabaseReturnValueModel
import json


class TestSteps():

    @classmethod
    def return_step_by_id(cls, step_id) -> DatabaseReturnValueModel:
        if step_id is None:
            return DatabaseReturnValueModel(
                executed=False,
                message="Not possible to acquire the step for this id.",
                error="No if was provided."
            )
        step, err = DatabaseConnector.return_step_by_id(int(step_id))
        if err:
            return DatabaseReturnValueModel(
                executed=False,
                message=f"Step {step_id} not found",
                error=err
            )

        return DatabaseReturnValueModel(
            executed=True,
            message=f"Step {step_id} found",
            data=step
        )

    @classmethod
    def return_steps_from_test_cases(cls, test_case_id, test_case_version) -> DatabaseReturnValueModel:

        steps, err = DatabaseConnector.return_steps_from_testcase(
            int(test_case_id),
            int(test_case_version)
        )

        if (err):
            return DatabaseReturnValueModel(
                executed=False,
                message=f"It was not possible to read the steps fro the test {test_case_id} in the version {test_case_version}.",
                error=err
            )
        updated_steps = [dict(step) for step in steps]

        for i in range(len(steps)):
            updated_steps[i]["step_action"], updated_steps[i]["expected_value"] = cls.find_ghost_step(
                updated_steps[i]["step_action"],
                updated_steps[i]["expected_value"]
            )

        return DatabaseReturnValueModel(
            executed=True,
            message=f"Steps for the test {test_case_id} in the version {test_case_version}.",
            data=updated_steps
        )

    @classmethod
    def find_ghost_step(cls, action_text: str, expected_text: str):
        steps_required = []
        actions = []
        expecteds = []

        start_index = action_text.rfind("[ghost]")
        end_index = action_text.rfind("[/ghost]")

        while ((start_index > -1 and end_index > -1) and (start_index < end_index)):
            substitute = action_text[start_index:end_index+8]
            substitute_by = "{" + action_text[start_index+7:end_index] + "}"

            action_text = action_text.replace(substitute, substitute_by)
            actions.append(substitute_by)
            steps_required.append(substitute_by)

            start_index = action_text.rfind("[ghost]")
            end_index = action_text.rfind("[/ghost]")

        start_index = expected_text.rfind("[ghost]")
        end_index = expected_text.rfind("[/ghost]")

        while ((start_index > -1 and end_index > -1) and (start_index < end_index)):
            substitute = expected_text[start_index:end_index+8]
            substitute_by = "{" + expected_text[start_index+7:end_index] + "}"

            expected_text = expected_text.replace(substitute, substitute_by)
            expecteds.append(substitute_by)
            if (substitute_by not in steps_required):
                steps_required.append(substitute_by)

            start_index = expected_text.rfind("[ghost]")
            end_index = expected_text.rfind("[/ghost]")

        for step in steps_required:
            try:
                action, expected = cls.find_step_ghost(**json.loads(step))
                if step in actions:
                    action_text = action_text.replace(step, action)

                if step in expecteds:
                    expected_text = expected_text.replace(step, expected)
            except json.JSONDecodeError as e:
                print(
                    f"\nNot possible to generate ghost step due to a format error.\n {e}")

        return action_text, expected_text

    @classmethod
    def find_step_ghost(cls, step, testcase, version):
        step_info, err = DatabaseConnector.return_step_by_info(
            int(step),
            int(testcase),
            int(version)
        )

        if not step_info:
            return_data = f"[ghost]'step':{step},'testcase':{testcase},'version':{version}[/ghost]"
            print(
                f"Error while reading the step from the test case {testcase}, version {version} and position {step}. error: {err}")
            return return_data, return_data

        return step_info["step_action"], step_info["expected_value"]

    @classmethod
    def update_step_info(cls, step_id, actions_data, results_data) -> DatabaseReturnValueModel:

        step_update_error = DatabaseConnector.update_step_data(
            int(step_id),
            actions_data,
            results_data
        )

        if step_update_error:
            return DatabaseReturnValueModel(
                executed=False,
                message=f"It was not possible to update the step data id = {step_id}",
                error=step_update_error
            )

        return DatabaseReturnValueModel(
            executed=True,
            message=f"step id = {step_id} update successfuly",
        )

    @classmethod
    def create_new_step(cls, actions_data, results_data, test_id, version, previous_step_id) -> DatabaseReturnValueModel:

        all_steps = cls.return_steps_from_test_cases(
            int(test_id),
            int(version)
        )

        if (not all_steps.executed):
            return DatabaseReturnValueModel(
                executed=False,
                message=f"It was not possible to read all the steps from the test {test_id} version {version}.",
                error=all_steps.error
            )

        previous_step_position = 0

        # returns the step position of the last step from the tests
        if (all_steps.data):
            previous_step_position = all_steps.data[-1]["step_position"]

        # Enters if the step added is not the last one
        if (previous_step_id):
            previous_step_position = cls.return_step_by_id(
                previous_step_id).data["step_position"]

            cls.update_steps_positions(
                all_steps.data,
                int(previous_step_position)+1,
                1
            )

        new_step_id, err = DatabaseConnector.create_new_step(
            int(version),
            int(test_id),
            actions_data,
            results_data,
            int(previous_step_position)+1
        )

        if (new_step_id):
            return DatabaseReturnValueModel(
                executed=True,
                message="New step added.",
                data=new_step_id
            )

        return DatabaseReturnValueModel(
            executed=False,
            message="It was not possible to add the new step.",
            error=err
        )

    @classmethod
    def update_steps_positions(cls, steps_list: list[dict], specified_step_position: int, increment_value: int):
        """
        This function is used for reordering the steps from a particular test once another step was deleted or added in said test
        - steps_list: List of steps that should be updated
        - specified_step_position: Step position thta was added or deleted
        - increment_value: How many positions should the steps be moved. can also be negative
        """

        increment = 0
        for step in steps_list:
            if (step["step_position"] >= specified_step_position):
                increment = increment_value

            if (increment):
                DatabaseConnector.update_step_position(
                    step["id"],
                    int(step["step_position"]) + increment
                )

    @classmethod
    def delete_step(cls, step_id, test_id, test_version) -> DatabaseReturnValueModel:
        deleted_step = cls.return_step_by_id(int(step_id))

        if (not deleted_step.executed):
            return DatabaseReturnValueModel(
                executed=False,
                message="step {step_id} does not exist",
                error=deleted_step.error
            )

        err = DatabaseConnector.delete_test_step_from_database(int(step_id))
        all_steps = cls.return_steps_from_test_cases(
            int(test_id),
            int(test_version)
        )

        if (not err):
            cls.update_steps_positions(
                all_steps.data,
                deleted_step.data["step_position"],
                -1
            )

            return DatabaseReturnValueModel(
                executed=True,
                message=f"The step {step_id} was deleted succesfuly.",
            )

        return DatabaseReturnValueModel(
            executed=False,
            message=f"The step {step_id} was not deleted.",
            error=err
        )

    @classmethod
    def copy_steps_new_version(cls, test_id, current_version, new_version) -> DatabaseReturnValueModel:
        steps_to_copy = cls.return_steps_from_test_cases(
            int(test_id),
            current_version
        )

        if (not steps_to_copy.executed):
            return DatabaseReturnValueModel(
                executed=False,
                message=f"It was not possible to read the steps from the test {test_id} version {current_version}.",
                error=steps_to_copy.error
            )

        step_not_created = False
        for step in steps_to_copy.data:
            steps_created = cls.create_new_step(
                step["step_action"],
                step["expected_value"],
                int(test_id),
                int(new_version),
                False
            )

            if (not steps_created.executed):
                step_not_created = True

        if (step_not_created):
            return DatabaseReturnValueModel(
                executed=False,
                message="Some steps were not possible to copy",
                error="Some steps were not possible to copy"
            )

        return DatabaseReturnValueModel(
            executed=True,
            message="Alls steps were copied",
        )

    @classmethod
    def copy_steps(cls, previous_test_id, current_version, new_test_id) -> DatabaseReturnValueModel:
        steps_to_copy = cls.return_steps_from_test_cases(
            int(previous_test_id),
            current_version
        )

        if (not steps_to_copy.executed):
            return DatabaseReturnValueModel(
                executed=False,
                message=f"test with the id {previous_test_id} does not exist",
                error=steps_to_copy.error,
            )

        step_not_created = False

        for step in steps_to_copy.data:
            steps_created = cls.create_new_step(
                step["step_action"],
                step["expected_value"],
                int(new_test_id),
                1,
                False
            )

            if (not steps_created):
                step_not_created = True

        if (step_not_created):
            return DatabaseReturnValueModel(
                executed=False,
                message="some steps were not possible to copy.",
                error="some steps were not possible to copy."
            )

        return DatabaseReturnValueModel(
            executed=True,
            message="All steps were copied.",
        )

    @classmethod
    def reorder_steps_position(cls, steps_ids_in_order) -> DatabaseReturnValueModel:
        position = 1
        for step in steps_ids_in_order:
            error = DatabaseConnector.update_step_position(
                int(step),
                position
            )
            position = position + 1
            if (error):
                return DatabaseReturnValueModel(
                    executed=False,
                    message="Position not updated successfully",
                    error=f"Position not update for the step {step}.\n error: {error}",
                    data=None
                )

        return DatabaseReturnValueModel(
            executed=True,
            message="Position updated successfully",
            error="",
            data=None
        )
