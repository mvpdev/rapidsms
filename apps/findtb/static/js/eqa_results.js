/*
Used in specimen referal tracking when you register a incomming specimen.
If you set it as invalid, hide the registration form for the patient.
*/

$(document).ready(function() {

    
    $("'input[type=checkbox]:checked").each(
      function() {

          $this = $(this);
          $this.parent('td').siblings('td').children().attr('disabled', 'disabled' );
      }
    );
    
   var changeHandler = function(event) {
        
        $("'input[type=checkbox]").each(
          function() {

              $this = $(this);
              $this.parent('td').siblings('td').children().removeAttr('disabled', 'disabled' );
        });
    
        $("'input[type=checkbox]:checked").each(
          function() {

              $this = $(this);
              $this.parent('td').siblings('td').children().attr('disabled', 'disabled' );
        });
        
    }

    $("input:checkbox").change(changeHandler).keypress(changeHandler);
    
    /* To prevent the form from crashing */
    $("#results-form").submit(function() {
    
        $("input").removeAttr('disabled');
        $("select").removeAttr('disabled');
      
    });
   
});

