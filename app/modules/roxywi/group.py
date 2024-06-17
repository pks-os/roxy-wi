import app.modules.db.group as group_sql
import app.modules.roxywi.common as roxywi_common


def update_group(group_id: int, group_name: str, desc: str) -> None:
    if group_name == '':
        return roxywi_common.return_error_message()
    else:
        try:
            group_sql.update_group(group_name, desc, group_id)
            roxywi_common.logging('Roxy-WI server', f'The {group_name} has been updated', roxywi=1, login=1)
        except Exception as e:
            raise Exception(e)


def delete_group(group_id: int) -> str:
    group = group_sql.select_groups(id=group_id)
    group_name = ''

    for g in group:
        group_name = g.name

    if group_sql.delete_group(group_id):
        roxywi_common.logging('Roxy-WI server', f'The {group_name} has been deleted', roxywi=1, login=1)
        return 'ok'
