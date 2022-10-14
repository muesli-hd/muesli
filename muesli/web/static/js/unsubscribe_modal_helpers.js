$(document).ready(function() {
  $('#confirm_unsubscribe').on('show.bs.modal', function (event) {
    let button = $(event.relatedTarget) // Button that triggered the modal
    let text = button.data('modal-text');
    let href = button.data('href');
    let confirm_text = button.data('modal-button-text') || 'Austreten';
    let button_class = button.data('modal-button-class') || 'btn-danger';

    let modal = $(this);
    modal.find('.modal-body p').text(text);
    modal.find('#confirm_unsubscribe_modal_button').attr("href", href);
    modal.find('#confirm_unsubscribe_modal_button').html(confirm_text);
    modal.find('#confirm_unsubscribe_modal_button').attr('class', `btn ${button_class}`);
  })}
)