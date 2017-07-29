from utils import *


# Implement JSON endpoint for an arbitrary item
@app.route('/category/<int:category_id>/<int:item_id>/JSON')
def menuItemJSON(category_id, item_id):
    try:
        item = session.query(Items).filter_by(id=item_id).one()
        return jsonify(Item=item.serialize)
    except:
        return redirect('/')