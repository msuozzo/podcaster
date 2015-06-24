"""Interface for constructing text-based menus
"""
from podcaster.table import TextTable


def build_data_rows(ind_to_cmd, obj_lst, *data_series):
    """Return a table-like list of lists that displays the properties defined
    in `data_series` for each object in `obj_lst`

    Constructs a 'CMD' column based on the object indices using the ind_to

    ind_to_cmd: a function accepting a single integral parameter, returing a
        string used to identify the row
    obj_lst: a list of objects in the order they will be added to rows
    *data_series: a variable number of 3-tuples of the form (series_name, obj_to_data, data_to_str)
        where the latter two elements are functions converting object to
        data and data to a string, respectively.
    """
    rows = [['CMD'] + [name for name, _, _ in data_series]]
    for ind, obj in enumerate(obj_lst):
        row = [ind_to_cmd(ind)] + [fmt(extract(obj)) for _, extract, fmt in data_series]
        rows.append(row)
    return rows


def build_menu(title, data_rows=None, action_rows=None):
    """Builds a menu in the following style:
    +--------------------+
    |        Title       | <--title
    +--------------------+
    | CMD1 |  C1  |  C2  | <--data header
    +------+------v------+
    | i    | d1   | d2   | <--other data rows
    +------+------^------+
    | ACTN | ACTN | ACTN | <--action rows
    +------+------+------+

    title: the title displayed in the top cell
    data_rows: a list of n-tuples (n >= 1 and is constant for all n-tuples)
        where the first n-tuple contains the data headers and all following
        n-tuples contain data rows
    action_rows: a list of 2-tuples (action, action_description)
    """
    menu = TextTable()

    # Add table title
    menu.add_break_row(seps=('+', '+'))
    menu.add_row((title,), align='c', seps=('|', '|'))
    menu.add_break_row(seps=('+', '+'))

    # Add data section
    if data_rows:
        num_cols = len(data_rows[0])
        def _gen_seps(normal_sep, data_sep):
            """Return the separator pattern for the `num_cols` columns:

                1 cols - (normal_sep, normal_sep)
                2 cols - (normal_sep, normal_sep, normal_sep)
                3 cols - (normal_sep, normal_sep, data_sep, normal_sep)
                4 cols - (normal_sep, normal_sep, data_sep, data_sep, normal_sep)
                etc.
            """
            num_data_seps = num_cols - 2  # tuple * negative_number = ()
            seps = 2 * (normal_sep,) + num_data_seps * (data_sep,)
            if num_cols > 1:
                seps += (normal_sep,)
            return seps

        name_seps = _gen_seps('|', '|')
        header_seps = _gen_seps('+', 'v')
        data_seps = _gen_seps('|', ' ')
        footer_seps = _gen_seps('+', '^')

        menu.add_row(data_rows[0], align='c', seps=name_seps)
        menu.add_break_row(seps=header_seps)
        menu.set_seps(*data_seps)
        for data_row in data_rows[1:]:
            menu.add_row(data_row)
        if len(data_rows) == 1:
            menu.add_row(('There\'s nothing here...',), seps=('?', '?'))
        menu.add_break_row(seps=footer_seps)

    # Add action section
    if action_rows:
        menu.set_seps('|', '|', '|')
        for action_row in action_rows:
            menu.add_row(action_row)
        menu.add_break_row(seps=('+', '+', '+'))

    return str(menu)
