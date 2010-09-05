/*
Used in specimen referal tracking when you register a incomming specimen.
If you set it as invalid, hide the registration form for the patient.
*/

$(document).ready(function() {

    
   var changeHandler = function() {
    
       if ( $('#id_chosen_action').val() == "received")
           $('.autohide').fadeIn('slow');
       else
           $('.autohide').fadeOut('slow');
    }

    $("#id_chosen_action").change(changeHandler).keypress(changeHandler);
    
   
});

