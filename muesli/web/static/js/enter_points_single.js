let student_results_json = document.currentScript.getAttribute('student_results_json');
let exercise_ids_json = document.currentScript.getAttribute('exercise_ids_json');
let show_tutor = document.currentScript.getAttribute('show_tutor');
let show_time = document.currentScript.getAttribute('show_time');
let ajax_submission_endpoint = document.currentScript.getAttribute('ajax_submission_endpoint');
let student_results;
let exercise_ids;
let latest_row_id = 0;

$(document).ready(function() {
    student_results = JSON.parse(student_results_json);
    exercise_ids = JSON.parse(exercise_ids_json);

    $('.student_select').select2({
        width: "16em"
    }).on('change', function () {
        let selectedStudents = getSelectedStudents(0);
        let points_captions = Array(exercise_ids.length + 1).fill('');
        let preselected_points = Array(exercise_ids.length + 1);
        for(let i = 0; i < selectedStudents.length; i++) {
            for(let j = 0; j < points_captions.length; j++) {
                let points = student_results[selectedStudents[i]]['points'][j];
                if (typeof(preselected_points[j]) === 'undefined') {
                    preselected_points[j] = {};
                    preselected_points[j].value = points;
                    preselected_points[j].alert = false;
                }
                if (preselected_points[j].value !== points) {
                    preselected_points[j].value = points;
                    preselected_points[j].alert = true;
                }
                let caption = points;
                if (points === 'None'){
                    caption = '-';
                }
                points_captions[j] += caption + '<br/>';
            }
        }

        $('.current-points').each(function (i, obj) {
            obj.innerHTML = (points_captions[i]);
            if (selectedStudents.length > 0) {
                if (i < preselected_points.length - 1 && preselected_points[i].alert) {
                    obj.style.color = 'red';
                } else {
                    obj.style.color = null;
                }
            }
        });
        $('.points').each(function (i, obj) {
            if (selectedStudents.length > 0) {
                if (obj.value === '') {
                    if (preselected_points[i].value !== 'None') {
                        obj.value = (preselected_points[i].value);
                    }
                }
            } else {
                obj.value = '';
            }
        });
        update_total(0);
    }).trigger('change');

    $(document).on('keydown', 'form', function(event) {
        let row_id;
        row_id = Number($(document.activeElement).closest('tr').attr('id').replace('row-', ''));
        if (event.key === "Enter") {
            return submit_all_points(row_id);
        }
        return true;
    });

    $(".select2-search__field").focus().select();
});

function update_total(row_id) {
    let total = 0;
    let current = 0;
    let row = $(`#row-${row_id}`);
    row.find(".points").each(function() {
        current = parseFloat(this.value.replace(/,/, "."));
        if (!isNaN(current)) {
            total += current;
        }
    });
    return row.find(".total").val(Number(total).toFixed(2));
}

function getSelectedStudents(row_id) {
    if (row_id === 0) {
        let selectedStudents = [];
        $('.student_select > option:selected').each(function() {
            selectedStudents.push($(this).val())
        });
        return selectedStudents;
    } else {
        return $('#row-' + row_id + ' button').attr('data-students').split(',')
    }
}

function update_student_names(row_id) {
    let row = $(`#row-${row_id}`);
    let students_str = row.find('button').attr('data-students');

    if (students_str === '') {
        row.remove();
        return true;
    }

    let students = students_str.split(',');
    let student_names = [];
    let student_names_field = row.find('.student-names');
    let student_names_html = '<table><tr>';

    students.forEach(function (student_id) {
        let current_student = '<td>';
        if (show_tutor) {
            current_student += student_results[student_id]['tutorial_tutor'] + '</td><td>';
        }
        if (show_time) {
            current_student += student_results[student_id]['tutorial_time'] + '</td><td>';
        }
        current_student += student_results[student_id]['name'];
        current_student += '</td>';
        student_names.push(current_student);
    });
    student_names_html += student_names.join('</tr><tr>');
    student_names_html += '</tr></table>';

    student_names_field.html(student_names_html);
}

function correct_row(row_id) {
    let row = $(`#row-${row_id}`);
    row.find('td[data-exercise]').each(function() {
        let cell = $(this);
        let value = cell.html();
        let exercise = cell.data('exercise');
        if (value === '-') {
            value = ''
        }
        cell.html(`<input type="text" class="points" name="points-${exercise}" value="${value}" size="3" onchange="update_total(${row_id})">`)
    });
    row.find('.total').html('<input class="total" readonly="readonly" size="4" value="0">');
    update_total(row_id);
    let button;
    button = row.find('button');
    button.text('Speichern');
    button.attr('onclick', `submit_all_points(${row_id})`);
}

function remove_students_from_previous_submissions(students) {
    let row_id;
    for (row_id = 1; row_id < latest_row_id; row_id++) {
        let button;
        let row_students;
        let new_row_students;
        let is_in_row;
        new_row_students = [];

        button = $('#row-' + row_id + ' button');
        if (button.length === 0) {
            continue;
        }
        row_students = button.attr('data-students').split(',');
        row_students.forEach(function(row_student) {
            is_in_row = false;
            students.forEach(function(student) {
                if (row_student === String(student)) {
                    is_in_row = true;
                }
            });
            if (!is_in_row) {
                new_row_students.push(row_student)
            }
        });
        button.attr('data-students', new_row_students.join(','));
        update_student_names(row_id)
    }

}

function submit_all_points(row_id) {
    let selectedStudents = getSelectedStudents(row_id);

    if ( selectedStudents.length === 0 ) {
        return true;
    }

    let submissionData = {};
    submissionData['student_id'] = selectedStudents.join(',');

    $(`#row-${row_id} .points`).each(function() {
        submissionData[this.getAttribute("name").replace("points-","")] = this.value;
    });

    let new_row_id = latest_row_id += 1;

    $.ajax(ajax_submission_endpoint,
        {
            data: submissionData,
            method: "POST",
            dataType: "json",
            success: function(response){
                let save_successful = true;
                if (response['format_error']) {
                    save_successful = false;
                }

                let insert_data = `<tr id='row-${new_row_id}'>`;

                // add student names
                insert_data += `<td class='student-names'></td>`;

                let sum_of_points = 0;
                for (let i=0; i < exercise_ids.length; i++) {
                    let p = response['submitted_points'][exercise_ids[i][1]];
                    if (p === undefined) {
                        $.toast({
                            type: "error",
                            title: `Konnte Punkte von Aufgabe ${exercise_ids[i][0]} nicht speichern`,
                            content: response["msg"],
                            delay: 10000
                        });
                        save_successful = false;
                        continue;
                    }
                    sum_of_points += p;
                    // Update cached points to the new server state
                    for (let j = 0; j < response['students'].length; j++) {
                        student_results[response['students'][j]]['points'][i] = (p === null) ? 'None' : p.toFixed(1);
                        student_results[response['students'][j]]['points'][exercise_ids.length] = sum_of_points.toFixed(1);
                    }
                    if (p === null) {
                        p = '-';
                    } else {
                        p = p.toFixed(1)
                    }
                    insert_data += '<td class="align-middle text-center" data-exercise="' + exercise_ids[i][1] +'">' + p + '</td>';
                }
                insert_data += `<td class="align-middle text-center total">${sum_of_points.toFixed(2)}</td>`;
                insert_data += `<td class="align-middle text-center"><button class="btn btn-primary" data-students="${response['students'].join(',')}" onclick="correct_row(${new_row_id})" type="button">Korrigieren</button></td>`;
                if (!save_successful) {
                    return false;
                }
                remove_students_from_previous_submissions(response['students']);
                $('#row-0').before(insert_data);
                update_student_names(new_row_id);
                if (row_id !== 0) {
                    $('#row-' + row_id).remove();
                }

                //deselect all students if a new row is submitted
                let student_select;
                student_select = $(".student_select");
                if (row_id === 0) {
                    let inputPunkte = document.getElementsByClassName('points');
                    for (let i = 0; i < inputPunkte.length; i++) {
                        inputPunkte[i].value = "";
                    }
                    student_select.val(null);
                    update_total(0);
                }

                student_select.trigger('change');
                $(".select2-search__field").focus().select();
                return true;
            },
            error: function(response){
                try {
                    $.snack("error", response, 10000);
                } finally {
                    $.snack("error", "Fehler: Konnte Punkte nicht speichern!", 10000);
                }
            }
        }
);

    return true;
}
