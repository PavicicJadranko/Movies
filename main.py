from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float, desc

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length
import requests
import json

with open('instance/Secret.json') as s:
    secrets = json.load(s)

app_key = secrets["SECRET_KEY"]
data_uri = secrets["SQLALCHEMY_DATABASE_URI"]


with open('instance/config.json') as f:
    config = json.load(f)

Auth = config


class EditForm(FlaskForm):
    rating = StringField('Your rating Out of 10', [DataRequired()])
    review = StringField('Your review', validators= [Length(min=1, max=75)])
    submit = SubmitField('Done')


class AddForm(FlaskForm):
    movie_title = StringField("Enter the name of the Movie.", [DataRequired()])
    submit = SubmitField('Add Movie 🎞️')


app = Flask(__name__)
app.config['SECRET_KEY'] = app_key
Bootstrap5(app)

# CREATE DB


class Base(DeclarativeBase):
    pass


app.config["SQLALCHEMY_DATABASE_URI"] = data_uri
db = SQLAlchemy(model_class=Base)
db.init_app(app)


# CREATE TABLE
class Movie(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    rating: Mapped[float] = mapped_column(Float, nullable=False)
    ranking: Mapped[int] = mapped_column(Integer, nullable=False)
    review: Mapped[str] = mapped_column(String(250), nullable=False)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)


with app.app_context():
    db.create_all()


@app.route("/")
def home():
    result = db.session.execute(db.select(Movie).order_by(Movie.rating))
    all_movies = result.scalars().all()

    for i in range(len(all_movies)):
        all_movies[i].ranking = len(all_movies) - i
    db.session.commit()

    return render_template("index.html", movies=all_movies)


@app.route("/edit", methods=["POST","GET"])
def edit():
    form = EditForm()
    movie_id = request.args.get("id")
    movie = db.get_or_404(Movie, movie_id)
    db.session.commit()
    if form.validate_on_submit():
        try:
            movie.rating = float(form.rating.data)
        except ValueError:
            movie.rating = movie.rating
        finally:
            movie.review = form.review.data
            db.session.commit()
        return redirect(url_for('home'))
    return render_template("edit.html", movie=movie, form=form)


@app.route("/delete")
def delete():
    movie_id = request.args.get("id")
    movie_to_delete = db.get_or_404(Movie, movie_id)
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for('home'))


@app.route("/add", methods=["POST", "GET"])
def add():
    add_form = AddForm()
    if add_form.validate_on_submit():
        movie_t = add_form.movie_title.data
        return redirect(url_for('select', movie_title=movie_t))
    return render_template("add.html", form=add_form)


@app.route("/select/<string:movie_title>", methods=["POST","GET"])
def select(movie_title):
    url = f"https://api.themoviedb.org/3/search/movie?query={movie_title}&include_adult=false&language=en-US&page=1"

    headers = Auth

    response = requests.get(url, headers=headers)
    response = response.json()
    response = response["results"]
    print(response)
    return render_template("select.html", movies=response)


@app.route("/save", methods=["POST", "GET"])
def save():
    new_movie = Movie(
        title=request.args.get("title"),
        year=request.args.get("year")[0:4],
        description=request.args.get("description"),
        rating=0,
        ranking=10,
        review=" ",
        img_url=f"https://image.tmdb.org/t/p/original{request.args.get("img_url")}"
    )
    db.session.add(new_movie)
    db.session.commit()
    return redirect(url_for('edit', id=new_movie.id))


if __name__ == '__main__':
    app.run(debug=True)
