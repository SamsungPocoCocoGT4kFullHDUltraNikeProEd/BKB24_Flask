from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import SubmitField


class UploadForm(FlaskForm):
    # Разрешенные расширения
    allowed_extensions = [
        "jpg",
        "jpeg",
        "png",
        "gif",
        "pdf",
        "txt",
        "doc",
        "docx",
        "mp3",
        "mp4",
    ]

    file = FileField(
        "Выберите файл",
        validators=[
            FileAllowed(
                allowed_extensions, f'Разрешены только: {", ".join(allowed_extensions)}'
            )
        ],
    )
    submit = SubmitField("Загрузить")
