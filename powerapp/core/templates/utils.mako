<%def name="form(form_obj, button_text, button_icon)">
    <form method="POST" class="form-horizontal" role="form">
        %for field in form_obj:
            <div class="form-group ${'has-error' if field.errors else ''}">
                ${ field.label(class_="col-md-2 col-md-offset-2 control-label") }
                <div class="col-md-6">
                    ${ field(class_='form-control') }
                    %if field.description:
                        <span class="help-block">${ field.description|h }</span>
                    %endif
                    %if field.errors:
                        <p class="text-danger"> ${ ". ".join(field.errors) | h }</p>
                    %endif
                </div>
            </div>
        %endfor
        <div class="form-group">
            <div class="col-md-6 col-md-offset-4">
                ${ submit_button(button_text, icon=button_icon) }
            </div>
        </div>
    </form>
</%def>

<%def name="submit_button(text, type='success', icon=None)">
    <button type="submit" class="btn btn-${ type }">
        %if icon:
            <span class="glyphicon glyphicon-${ icon }"></span>
        %endif
        ${ text }
    </button>
</%def>
