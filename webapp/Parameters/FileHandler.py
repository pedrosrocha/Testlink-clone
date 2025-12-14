from ..utils.return_data_model import DatabaseReturnValueModel
from werkzeug.utils import secure_filename
import os


class files:

    @classmethod
    def savefile(cls, file, root_path) -> DatabaseReturnValueModel:
        """
        Saves the image sent from the frontend
        """
        filename = secure_filename(file.filename)
        upload_folder = os.path.join(root_path, 'Static', 'Uploads')
        os.makedirs(upload_folder, exist_ok=True)
        file_path = os.path.join(upload_folder, filename)

        try:
            file.save(file_path)
            return DatabaseReturnValueModel(
                executed=True,
                message="File saved successfully.",
            )

        except Exception as e:
            return DatabaseReturnValueModel(
                executed=False,
                message="It was not possible to save the file.",
                error=e
            )
