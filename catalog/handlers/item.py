from utils import *


# Show the description of a certain item
@app.route('/category/<int:category_id>/<int:item_id>')
@user_logged_in
def showItem(category_id, item_id, uid):
    categories = session.query(Category).order_by(asc(Category.name))
    category = session.query(Category).filter_by(id=category_id).one()
    item = session.query(Items).filter_by(id=item_id).one()
    return render_template('item.html', categories=categories, category=category, item=item)


# Create a new item for a category
@app.route('/category/items/new/', methods=['GET', 'POST'])
@user_logged_in
def newItem(category_id, item_id, uid):
    categories = session.query(Category).all()
    if request.method == 'POST':
        if request.form['name'] == "" or request.form['description'] == "":
            flash('Please fill in a item name and a description')
            return render_template('newitem.html', categories=categories)
        category = request.form['category']
        category_id = session.query(Category).filter_by(name=category).one().id
        newItem = Items(
            name=request.form['name'], description=request.form['description'], category_id=category_id, user_id=uid) #user_id=login_session['user_id'])
        session.add(newItem)
        flash('New Item %s Successfully Created' % newItem.name)
        session.commit()
        return redirect(url_for('showCategories'))
    else:
        return render_template('newitem.html', categories=categories)


# Edit a certain item
@app.route('/category/<int:category_id>/<int:item_id>/edit/', methods=['GET', 'POST'])
@user_logged_in
@item_exists
@item_owned
def editItem(category_id, item_id):
    item = session.query(Items).filter_by(id=item_id).one()
    if category_id != item.category_id:
        return abort(404)
    if request.method == 'POST':
        if (request.form['name'] == "" or request.form['description'] == "") and request.form['submit'] == "submit":
            flash('Please fill in a item name and a description')
            return render_template('edititem.html', item=item)
        if request.form['submit'] == "submit":
            item.name = request.form['name']
            item.description = request.form['description']
            session.add(item)
            flash('Item %s successfully edited' % item.name)
            session.commit()
        return redirect(url_for('showCategories'))
    else:
        return render_template('edititem.html', item=item)


# Delete a certain item
@app.route('/category/<int:category_id>/<int:item_id>/delete/', methods=['GET', 'POST'])
@user_logged_in
@item_exists
@item_owned
def deleteItem(category_id, item_id):
    # if 'username' not in login_session:
    #     return redirect('/login')
    category = session.query(Category).filter_by(id=category_id).one()
    item = session.query(Items).filter_by(id=item_id).one()
    if category_id != item.category_id:
        return abort(404)
    if request.method == 'POST':
        if request.form['submit'] == "delete":
            session.delete(item)
            session.commit()
            flash('Item %s has been successfully deleted from category %s' % (item.name, category.name))
        return redirect(url_for('showCategories'))
    else:
        return render_template('deleteitem.html', category=category, item=item)
