from app import app, db
from app.db import Recipe
from app.forms import RecipeForm
from flask import render_template, flash, redirect, request, make_response


@app.route("/admin/sampledata")
def load_sample_data():
    db.import_sample_data()
    return redirect("/index")


@app.route("/")
@app.route("/index")
def index():
    recipes = Recipe.find({})
    return render_template("index.html", title="Home", recipes=recipes)


@app.route("/search", methods=["POST"])
def search():
    data = request.form["recipe_search"]
    if data:
        results = Recipe.__collection__.find({"$text": {"$search": data}}).limit(10)
        return render_template("search.html", results=results)

    return "Notfound", 404


@app.route("/recipe/<id>")
def recipe(id):
    recipe = Recipe.get_doc(object_id=id)
    if recipe:
        return render_template("details.html", title=recipe.name, recipe=recipe)

    return render_template("404.html"), 404


@app.route("/recipe/<id>/edit", methods=["GET", "POST"])
def edit_recipe(id):
    recipe = Recipe.get_doc(object_id=id)
    form = RecipeForm(obj=recipe)
    if form.validate_on_submit():
        form.populate_obj(recipe)
        recipe.save()

        flash('Recipe "{}" saved succesfully'.format(form.name.data))
        return redirect("/recipe/{}".format(recipe._id))

    return render_template("edit.html", title="Edit recipe", form=form, rec_id=id)


@app.route("/recipe/delete", methods=["POST"])
def delete_recipe():
    id = request.form["id"]
    recipe = Recipe.get_doc(object_id=id)
    if recipe:
        recipe_name = recipe.name
        recipe.remove()
        flash('Recipe "{}" removed successfully'.format(recipe_name))
        return redirect("/index")

    flash('There was a problem removing recipe with id "{}"'.format(id))
    return redirect("/index")


@app.route("/recipe/new", methods=["GET", "POST"])
def new_recipe():
    form = RecipeForm()
    if form.validate_on_submit():
        recipe = Recipe()
        form.populate_obj(recipe)
        recipe.save()

        flash("Recipe {} saved successfully".format(form.name.data))
        return redirect(f"/recipe/{recipe._id}")

    return render_template("edit.html", title="Create recipe", form=form)


@app.route("/image/upload", methods=["POST"])
def upload_image():
    recipe_id = request.form["recipe_id"]
    filename = request.form["filename"]
    if recipe_id and filename:
        file = request.files["file"]
        contents = file.read()
        db.store_image(filename=filename, contents=contents)

        flash("Cover image updated successfully!")
        return redirect(f"/recipe/{recipe_id}/edit")

    flash("Create and save the recipe before uploading the cover image.")
    return redirect("/recipe/new")


@app.route("/image/remove", methods=["POST"])
def remove_image():
    recipe_id = request.form["recipe_id"]
    filename = request.form["filename"]
    if recipe_id and filename:
        db.remove_images(filename=filename)

        flash("Cover image deleted successfully!")
        return redirect(f"/recipe/{recipe_id}/edit")

    flash("Create and save the recipe before uploading the cover image.")
    return redirect("/index")


@app.route("/image/<id>.jpg")
def image(id):
    image = db.read_image(id)
    response = make_response(image)
    response.headers.set("Content-Type", "image/jpeg")
    response.headers.set("Content-Disposition", "attachment", filename="%s.jpg" % id)
    return response
