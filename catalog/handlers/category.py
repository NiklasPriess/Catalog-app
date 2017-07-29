from utils import *


# Show items of a certain category
@app.route('/category/<int:category_id>')
@user_logged_in
def showCategory(category_id, item_id, uid):
    categories = session.query(Category).order_by(asc(Category.name))
    category = session.query(Category).filter_by(id=category_id).one()
    items = session.query(Items).filter_by(category_id=category_id).all()
    return render_template('category.html', categories=categories, category=category, items=items)

# Create a new category
@app.route('/category/new/', methods=['GET', 'POST'])
@user_logged_in
def newCategory(category_id, item_id, uid):
    if request.method == 'POST':
        if request.form['name'] == "":
            flash('Please fill in a category name')
            return render_template('newcategory.html')
        newCategory = Category(
            name=request.form['name'], user_id=uid) #user_id=login_session['user_id'])
        session.add(newCategory)
        flash('New Category %s Successfully Created' % newCategory.name)
        session.commit()
        return redirect(url_for('showCategories'))
    else:
        return render_template('newcategory.html')


# Edit a Category
@app.route('/category/<int:category_id>/edit', methods=['GET', 'POST'])
@user_logged_in
@category_exists
@category_owned
def editCategory(category_id):
    category = session.query(Category).filter_by(id=category_id).one()
    if request.method == 'POST':
        if request.form['name'] == "" and request.form['submit'] == "submit":
            flash('Please fill in a category name')
            return render_template('editcategory.html', category=category)
        if request.form['submit'] == "submit":
            category.name = request.form['name']
            session.add(category)
            flash('Category %s successfully edited' % category.name)
            session.commit()
        return redirect(url_for('showCategories'))
    else:
        return render_template('editcategory.html', category=category)


# Delete a Category
@app.route('/category/<int:category_id>/delete', methods=['GET', 'POST'])
@user_logged_in
@category_exists
@category_owned
def deleteCategory(category_id):
    # if 'username' not in login_session:
    #     return redirect('/login')
    category = session.query(Category).filter_by(id=category_id).one()
    items = session.query(Items).filter_by(category_id=category_id).all()
    print items
    if request.method == 'POST':
        if request.form['submit'] == "delete":
            session.delete(category)
            for item in items:
                session.delete(item)
            session.commit()
            flash('Category %s and associated items have been successfully deleted' % category.name)
        return redirect(url_for('showCategories'))
    else:
        return render_template('deletecategory.html', category=category, items=items)