from app import app
from app.db import Recipe, import_sample_data, read_image
from app.forms import RecipeForm
from flask import render_template, flash, redirect, request, make_response


@app.route("/")
@app.route("/index")
def index():
    recipes = Recipe.find({})
    return render_template("index.html", title="Home", recipes=recipes)


@app.route("/admin/sampledata")
def load_sample_data():
    import_sample_data()
    return redirect("/index")


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


@app.route("/image/<id>.jpg")
def image(id):
    image = read_image(id)
    response = make_response(image)
    response.headers.set("Content-Type", "image/jpeg")
    response.headers.set("Content-Disposition", "attachment", filename="%s.jpg" % id)
    return response


@app.route("/edit/recipe/<id>", methods=["GET", "POST"])
def edit_recipe(id):
    recipe = Recipe.get_doc(object_id=id)
    form = RecipeForm(obj=recipe)
    if form.validate_on_submit():
        form.populate_obj(recipe)
        recipe.save()

        flash('Recipe "{}" saved succesfully'.format(form.name.data))
        return redirect("/recipe/{}".format(recipe._id))

    return render_template("edit.html", title="Edit recipe", form=form)


@app.route("/delete/recipe", methods=["POST"])
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


@app.route("/new/recipe", methods=["GET", "POST"])
def new_recipe():
    form = RecipeForm()
    if form.validate_on_submit():
        recipe = Recipe()
        form.populate_obj(recipe)
        recipe.save()

        flash("Recipe {} added successfully".format(form.name.data))
        return redirect("/index")

    return render_template("edit.html", title="Create recipe", form=form)
