$(document).ready(function() {

    
   $('#district-selector input').remove()
   $('#zone-selector input').remove() 
   
   $('#zone-selector').css('float', 'left')
                      .css('padding-left', '4em')
    
   var change_district = function() {
    
       $('#district-selector').submit();

           
       /* location.reload(); */
    }

    $("#district-selector select").change(change_district).keypress(change_district);
    
   
    var change_zone = function() {
    
       $('#zone-selector').submit();
           
       /* location.reload(); */
    }

    $("#zone-selector select").change(change_zone).keypress(change_zone);
   
});

