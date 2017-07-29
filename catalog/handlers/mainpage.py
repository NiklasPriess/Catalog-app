from utils import *


# Mainpage show all categories and items that were added last
@app.route('/')
@app.route('/category/')
def showCategories():
	categories = session.query(Category).order_by(asc(Category.name))
	latestitems = session.query(Items).order_by(desc(Items.id)).limit(10).all()
	print "TEST"
	return render_template('mainpage.html', categories=categories, latestitems=latestitems)

