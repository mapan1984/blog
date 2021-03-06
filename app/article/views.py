from flask import flash, render_template, redirect, url_for, request, abort
from flask_login import current_user, login_required


from app import db, redis
from app.models import Article, Comment, Permission, Rating
from app.decorators import permission_required, author_required
from app.article import article as article_blueprint
from app.article.forms import EditArticleForm, ModifyArticleForm
from app.tasks import build_index, rebuild_index


@article_blueprint.route('/<title>', methods=['GET'])
def article(title):
    """ 显示单篇文章 """
    article = Article.query.filter_by(title=title).first_or_404()

    # 相似文章
    sim_articles = redis.zrevrange(article.title, 0, 4, withscores=True)

    # 获取评分情况
    ratings = article.ratings.all()
    num_rating = len(ratings)
    try:
        avg_rating = sum(map(lambda rating: rating.value, ratings)) / num_rating
    except ZeroDivisionError:
        avg_rating = None

    try:
        current_user_rating = article.ratings.filter_by(user=current_user).first().value
    except AttributeError:
        current_user_rating = None

    try:
        current_user_id = current_user.id
    except AttributeError:
        current_user_id = None

    return render_template('article/article.html', article=article,
                           sim_articles=sim_articles,
                           num_rating=num_rating, avg_rating=avg_rating,
                           current_user_rating=current_user_rating,
                           article_id=article.id, user_id=current_user_id)


@article_blueprint.route('/edit', methods=['GET', 'POST'])
@author_required
def edit():
    form = EditArticleForm()
    if form.validate_on_submit():
        article = Article(
            title=form.title.data,
            # TODO: delete
            name=form.title.data,
            body=form.body.data,
            author=current_user._get_current_object()
        )
        article.set_category(form.category.data)
        article.add_tags(form.tags.data.strip().split(' '))
        db.session.add(article)
        db.session.commit()
        build_index.delay(article.id)
        return redirect(url_for('article.article', title=article.title))
    return render_template('article/edit.html', form=form)


@article_blueprint.route('/delete/<title>')
@author_required
def delete(title):
    article = Article.query.filter_by(title=title).first_or_404()
    if current_user != article.author \
            and not current_user.can(Permission.ADMINISTER):
        abort(403)
    else:
        flash(article.delete())
        return (redirect(request.args.get('next')
                or url_for('user.user', username=current_user.username)))


@article_blueprint.route('/modify/<title>', methods=['GET', 'POST'])
@author_required
def modify(title):
    article = Article.query.filter_by(title=title).first_or_404()
    form = ModifyArticleForm(article=article)
    if current_user != article.author \
            and not current_user.can(Permission.ADMINISTER):
        abort(403)
    if form.validate_on_submit():
        article.title = form.title.data
        # TODO: delete
        if article.name is None:
            article.name = form.title.data
        article.body = form.body.data

        article.set_category(form.category.data)

        article.delete_tags()
        article.add_tags(form.tags.data.split(' '))

        db.session.add(article)
        db.session.commit()

        rebuild_index.delay(article.id)

        flash('您的文章已经成功修改')
        return redirect(url_for('article.article', title=article.title))
    form.title.data = article.title
    form.category.data = article.category.id
    form.tags.data = " ".join(tag.name for tag in article.tags)
    form.body.data = article.body
    return render_template('article/edit.html', form=form)


@article_blueprint.route('/rating', methods=['POST'])
@login_required
def rating():
    user_id = request.json['user_id']
    rating_value = request.json['rating_value']
    article_id = request.json['article_id']
    rating = Rating.query.filter_by(user_id=user_id, article_id=article_id).first()
    if rating is None:  # 新建
        rating = Rating(value=rating_value, user_id=user_id, article_id=article_id)
    else:  # 更改
        rating.value = rating_value
    db.session.add(rating)
    return "Rating done."


@article_blueprint.route('/comment', methods=['POST'])
@login_required
def comment():
    user_id = request.form['user_id']
    article_id = request.form['article_id']
    comment_body = request.form['comment_body']
    comment = Comment(body=comment_body, article_id=article_id, author_id=user_id)
    db.session.add(comment)
    flash("你的评论已提交")
    return redirect(request.args.get('next') or url_for('main.index'))


@article_blueprint.route('/moderate/<comment_id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    if comment.article.author == current_user\
            or comment.author == current_user\
            or current_user.is_administrator:
        db.session.delete(comment)
        flash('评论已经删除')
    return redirect(url_for('article.article', title=comment.article.title))
