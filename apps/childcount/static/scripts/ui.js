
var clog = function(){}
var cerr = function(){}
var debug = false;

if(typeof(console)!=='undefined' && debug) {clog = console.log; cerr = console.error; }

dataentry_forms = [];
dataentry_form = null;f

function load_json_forms()
{
    dataentry_forms = [];

    dataentry_forms.push(formfree);

    for (var i in forms)
    {
        var form_fields = [];
        var form_id = forms[i];
        // JSON request
        $.ajax({
            url: FORM_URL.replace('FORMID', forms[i]),
            dataType: 'json',

            async: false,
            success: function (data) { if (data) { form_fields = data['fields']; form_id = data['id']} }
        });

        var form_obj = new ChildCountForm(form_id);

        var s = new ChildCountFormSection('root', 'root', 'root');
        for (var fid in form_fields)
        {
            var ff = form_fields[fid];
            if (ff['type'] == 's')
            {
                form_obj.addSection(s);
                var s = new ChildCountFormSection(ff['id'], ff['name'], ff['title']);
            }
            if (ff['type'] == 'f')
            {
                var f = new ChildCountFormField(ff['id'], ff['name'], ff['title']);
                s.addField(f);
            }
        }
        form_obj.addSection(s);

        dataentry_forms.push(form_obj);
    }

    // init archives
    dataentry_archives = {};

    // init duplicates
    for (var i in dataentry_forms)
    {
        var f = dataentry_forms[i];
        SMSes[f.name] = [];
    }

}

function save_form(form)
{
    if (form == null)
        return false;

    var arch_id = dataentry_form.name;

    // save window
    dataentry_archives[arch_id] = {'history': '', 'feedback': '', 'current': 0}
    var doc = document.getElementById('ccform')
    dataentry_archives[arch_id].history = doc.innerHTML;

    var doc = document.getElementById('feedback')
    dataentry_archives[arch_id].feedback = doc.innerHTML;

    dataentry_archives[arch_id].current = current;

    return true;
}

function load_form(form)
{
    if (dataentry_archives[form.name] == null)
        return false;

    var arch = dataentry_archives[form.name];
    var ccform_txt = arch.history;
    var feedback_txt = arch.feedback;

    reset_tables(ccform_txt, feedback_txt);

    current = arch.current;
    return true;
}

function switch_forms(index)
{
    save_form(dataentry_form);

    // switch data
    dataentry_form = dataentry_forms[index];
    dataentry_form.index = index;

    // restore backup or generate
    if (!load_form(dataentry_form))
    {

        // change window
        reset_tables();
        // gen header row
        gen_table(0);

        // init counter and gen current row
        current = 1;
        gen_table(current);
    }

    // highlight
    highlight_buttons(dataentry_form);

    // scrollTo last history
    $('#ccform_body').scrollTo('#sms_'+current, 1)

    // parse input
    parse_message();

    // focus on entry, let's go
    focus_entry();
}

function highlight_buttons(form)
{
    for (var i in dataentry_forms)
    {
        var doc = document.getElementById('button_' + dataentry_forms[i].name);
        doc.className = (dataentry_forms[i] == form) ? 'hover' : '';
    }
}

function gen_forms_link()
{
    var doc = document.getElementById('form_buttons');
    for (var i in dataentry_forms)
    {
        var myform = dataentry_forms[i];
        clog(myform);
        var txt = '';
        for (var z in dataentry_forms[i].name) { txt += dataentry_forms[i].name[z] + '<br />'; }
        var snippet = '<li id="button_' + dataentry_forms[i].name + '" onclick="switch_forms(' + i + ');">' + txt + '</li>';
        clog(snippet);
        clog(myform.displayName());
        doc.innerHTML += snippet;           
    }
}


function focus_entry()
{
    $('#message').focus();
}

function duplicate_sms(id)
{
    // copy text from history (SMSes) to input field
    $('#message').val(SMSes[dataentry_form.name][id].message);
    parse_message();
    focus_entry();
}

function form_focus(event)
{
    clog("event: " +event.keyCode)
    target = String.fromCharCode(event.keyCode).toLowerCase();
    clog("target: " + target);
    switch_forms(parseInt(target) - 1); 
}


function loadUI() {

    // load forms
    load_json_forms();

    // add UI shortcuts
    shortcut.add("Ctrl+Enter", focus_entry);

    // add links and shortcuts
    for (var i in dataentry_forms)
    {
        shortcut.add("Ctrl+" + (parseInt(i) + 1), form_focus);
    }
    gen_forms_link();

    // launch first form
    current = 1;
    switch_forms(0);

}

function size_adjust()
{

    var overhead = 160;
    var window_height = window.outerHeight;
    var available_height = window_height - overhead;

    clog("window_height: "+window_height);
    clog("available_height: "+available_height);

    var body_height = Math.round(available_height / 3);
    var msg_height = Math.round(available_height / 20);

    clog("body_height: "+body_height);
    clog("msg_height: "+msg_height);

    var doc = document.getElementById('ccform_body');
    doc.style.height = body_height + 'px';

    var doc = document.getElementById('log');
    doc.style.height = body_height + 'px';

    var doc = document.getElementById('message');
    doc.style.height = msg_height + 'px';
}
