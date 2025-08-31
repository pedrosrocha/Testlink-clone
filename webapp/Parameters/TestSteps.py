
from .Database.steps_database import DatabaseConnector
from ..utils.return_data_model import DatabaseReturnValueModel
from datetime import datetime


class TestSteps():

    @classmethod
    def return_step_by_id(cls, step_id):
        try:
            step = DatabaseConnector.return_step_by_id(int(step_id))
            return step,  f"Step{step_id} found"
        except:
            return False, f"No step was found for the id {step_id}"

    @classmethod
    def return_steps_from_test_cases(cls, test_case_id, test_case_version):

        try:
            steps = DatabaseConnector.return_steps_from_testcase(
                int(test_case_id),
                int(test_case_version)
            )

            return True, steps

        except:
            return False, f"No steps found for the test case id = {test_case_id} and version = {test_case_version}"

    @classmethod
    def update_step_info(cls, step_id, actions_data, results_data):
        try:
            DatabaseConnector.update_step_data(
                int(step_id),
                actions_data,
                results_data)
            return True, "step updated"
        except:
            return False, f"No steps found for the id = {step_id}"

    @classmethod
    def create_new_step(cls, actions_data, results_data, test_id, version, previous_step_id):

        all_steps = cls.return_steps_from_test_cases(
            int(test_id),
            int(version)
        )

        if (not all_steps[0]):
            return False, all_steps[1]

        previous_step_position = 0

        # returns the step position of the last step from the tests
        if (all_steps[1]):
            previous_step_position = all_steps[1][-1]["step_position"]

        # Enters if the step added is not the last one
        if (previous_step_id):
            previous_step_position = cls.return_step_by_id(previous_step_id)[
                0].step_position

            cls.update_steps_positions(
                all_steps[1],
                int(previous_step_position)+1,
                1
            )

        result = DatabaseConnector.create_new_step(
            int(version),
            int(test_id),
            actions_data,
            results_data,
            int(previous_step_position)+1
        )

        if (result):
            return True, "New step added successfully"

        return False, "It was not possible to create the new step"

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
            if (step.step_position >= specified_step_position):
                increment = increment_value

            if (increment):
                DatabaseConnector.update_step_position(
                    step.id,
                    int(step.step_position) + increment
                )

    @classmethod
    def delete_step(cls, step_id, test_id, test_version):
        deleted_step = cls.return_step_by_id(int(step_id))[0]

        if (not deleted_step):
            return False, f"step {step_id} does not exist"

        result = DatabaseConnector.delete_test_step_from_database(int(step_id))
        all_steps = cls.return_steps_from_test_cases(
            int(test_id),
            int(test_version)
        )[1]

        if (result):
            cls.update_steps_positions(
                all_steps,
                deleted_step.step_position,
                -1
            )

            return True, f"step {step_id} deleted successfully"

        return False, f"step {step_id} was not deleted"

    @classmethod
    def copy_steps_new_version(cls, test_id, current_version, new_version):
        steps_to_copy = cls.return_steps_from_test_cases(
            int(test_id),
            current_version
        )

        if (not steps_to_copy[0]):
            return False, f"test with the id {test_id} does not exist"

        step_not_created = False
        for step in steps_to_copy[1]:
            steps_created = cls.create_new_step(
                step.step_action,
                step.expected_value,
                int(test_id),
                int(new_version),
                False
            )

            if (not steps_created):
                step_not_created = True

        if (step_not_created):
            return False, f"Some steps were not possible to copy"

        return True, "All steps were copied"

    @classmethod
    def copy_steps(cls, previous_test_id, current_version, new_test_id):
        steps_to_copy = cls.return_steps_from_test_cases(
            int(previous_test_id),
            current_version
        )

        if (not steps_to_copy[0]):
            return False, f"test with the id {previous_test_id} does not exist"

        step_not_created = False

        for step in steps_to_copy[1]:
            steps_created = cls.create_new_step(
                step.step_action,
                step.expected_value,
                int(new_test_id),
                1,
                False
            )

            if (not steps_created):
                step_not_created = True

        if (step_not_created):
            return False, f"Some steps were not possible to copy"

        return True, "All steps were copied"

    @classmethod
    def reorder_steps_position(cls, steps_ids_in_order) -> DatabaseReturnValueModel:
        position = 1
        for step in steps_ids_in_order:
            data_response = DatabaseConnector.update_step_position(
                int(step),
                position
            )
            position = position + 1
            if (not data_response):
                return DatabaseReturnValueModel(
                    executed=False,
                    message="Position not updated successfully",
                    error=f"Position not update for the step {step}",
                    data=None
                )

        return DatabaseReturnValueModel(
            executed=True,
            message="Position updated successfully",
            error="",
            data=None
        )
