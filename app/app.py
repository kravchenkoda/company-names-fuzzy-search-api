from flask import Flask

app = Flask(__name__)


@app.route('/companies/<int:id>', methods=['GET', 'PATCH', 'DELETE'])
def get_update_delete(id: int):
    pass

@app.route('/companies', methods=['GET', 'POST', 'PATCH'])
def single_search_single_add_bulk_add_bulk_update():
    pass

@app.route('/companies/multi-search', methods=['POST'])
def multisearch():
    pass

@app.route('/companies/bulk-delete')
def bulk_delete():
    pass

if __name__ == '__main__':
    app.run(debug=True, port=5000)
