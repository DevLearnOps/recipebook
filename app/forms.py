from flask_wtf import FlaskForm
from wtforms import validators, StringField, SubmitField, TextAreaField


class RecipeForm(FlaskForm):
    """
    A class to represent the web form to create and edit recipes
    """

    name = StringField(
        "Name", validators=[validators.InputRequired(), validators.length(max=256)]
    )
    ingredients = TextAreaField("Ingredients", validators=[validators.optional()])
    directions = TextAreaField("Directions", validators=[validators.optional()])
    submit = SubmitField("Save", name="save")
