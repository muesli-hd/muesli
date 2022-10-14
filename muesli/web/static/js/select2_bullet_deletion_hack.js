$(document).ready(function() {
    // The following is some boilerplate to enable select2 and let backspace remove a bullet instead of converting it to text
    // See https://github.com/select2/select2/issues/3354
    $.fn.select2.amd.require(['select2/selection/search'], function (Search) {
        var oldRemoveChoice = Search.prototype.searchRemoveChoice;

        Search.prototype.searchRemoveChoice = function () {
            oldRemoveChoice.apply(this, arguments);
            this.$search.val('');
        };

        $('.custom-multi-select').select2();
    });
});
