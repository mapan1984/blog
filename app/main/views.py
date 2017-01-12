import os

from flask import render_template, current_app, session

from app.main import main
from app.models import Category, Tag, Article

@main.route('/')
def index():
    """主页"""
    page_num = 1
    start, end = 2*page_num - 2, 2*page_num
    content_list = []
    for article in Article.query.all()[start:end]:
        with open(article.ds_path, "r", encoding='utf-8') as fd:
            content_list.append(fd.read())
    content = "".join(content_list)
    return render_template('index.html',
                           page_num=page_num,
                           content=content)

@main.route('/categories')
def categories():
    category_articles = {}
    categories = [category for category in Category.query.all()]
    for category in categories:
        category_articles[category] = \
                Article.query.filter_by(category=category).all()
    return render_template('category.html',
                           category_articles=category_articles)

@main.route('/tag')
def tag():
    return render_template('tag.html')

@main.route('/news')
def news():
    return render_template('news.html')

@main.route('/about')
def about():
    return render_template('about.html')
