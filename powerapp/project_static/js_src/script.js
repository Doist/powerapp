$(function() {
    $(".powerapp-usermenu").dropdown();
    $('select').not('.disabled').material_select();
    $("#logout-link").click(function() {$("#logout-form").submit(); return false});
    $.each(django_messages || [], function(i, obj) {
        Materialize.toast(escapeHTML(obj.message), 4000);
    });
});
