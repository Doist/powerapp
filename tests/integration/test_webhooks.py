# -*- coding: utf-8 -*-


def test_webhook(api, catcomments_integration, ngrok):
    # add a new item to the inbox
    item = api.items.add('test', api.user.get('inbox_project'))
    api.commit()
    # wait for the update
    # 1. api.commit() creates a new task
    # 2. Todoist sends a webhook back to the application
    # 3. application runs the catcomment integratoin
    # 4. the integration adds a new comment to the post,
    #    and the client can see the update in seq_no
    api.wait_for_update(resource_types=['notes'])
    assert len(api.notes.all()) == 1
    note = api.notes.all()[0]
    assert 'http://thecatapi.com/' in note['content']
