# -*- coding: utf-8 -*-
#
# muesli/allocation.py
#
# This file is part of MUESLI.
#
# Copyright (C) 2008, Kilian Kilger <kilian (at) nihilnovi.de>
# Copyright (C) 2011, Matthias Kuemmerer <matthias (at) matthias-k.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import muesli
from muesli import utils, models

import tempfile
import subprocess

class Node:
    def __init__(self, type=type, id=-1, time=None, extra=None, tutorials=None):
        self.type = type
        self.id = id
        self.time = time
        self.extra = extra
        self.tutorials=tutorials
    def __repr__(self):
        return "<Node. Type: '%s', time: %s" % (self.type, self.time)

class StudentNode(Node):
    def __init__(self, student=None, *args, **kwargs):
        Node.__init__(self, *args, **kwargs)
        self.type='student'
        self.student = student

class Arc:
    def __init__(self, src, dest, priority=None, type=None, extra=None):
        self.src=src
        self.dest=dest
        self.priority=priority
        self.type=type
        self.extra=extra

"""
 solves the minimum-cost network flow problems
"""
class Allocation:
    def __init__(self, lecture):
        self.lecture = lecture
        self.session = models.Session.object_session(self.lecture)
    def doAllocation(self):
        if not self.lecture.mode == 'prefs':
            raise Exception('Lecture not in preference mode')
        nodes = []
        arcs = []
        # every object in our optimization problem is a 'node'
        # the first node we add is the master node. The master node
        # is the destination for all network flow
        nodes.append(Node(
                type='master',
                id = -1,
                time = None  ## XXX: make catalyst happy!
                ))
        # the next node is the 'ghost' node. it is a 'fake-time' which
        # is needed that our optimization problem _always_ has a solution.
        # there is always an arc from 'ghost' to 'master'.
        nodes.append(Node(
                type  = 'time',
                id    = -1,
                extra = 'ghost',
                time  = None
                ))
        arcs.append(Arc(1,0,
                priority = utils.ghostcapacity,
                type= 'times=>master'
                ))
        # we do now add nodes for all different 'times' where
        # tutorials are happening. Every time gets an arc to the
        # master node.
        times = self.lecture.prepareTimePreferences()
        for time in times:
            time_tutorials = []
            tuts = self.session.query(models.Tutorial).filter(models.Tutorial.lecture_id==self.lecture.id).filter(models.Tutorial.time == time['time']).all()
            for tut in tuts:
                time_tutorials.append({
                        'id': tut.id,
                        'tutorial': tut,
                        'max_students': tut.max_students,
                        'act_students': 0
                        })
            if time_tutorials:
                nodes.append(Node(
                        type='time',
                        time=time['time'],
                        tutorials=time_tutorials
                        ))
                arcs.append(Arc(len(nodes)-1, 0,
                        priority = time['max_students'],
                        type = 'times=>master',
                        extra = ''
                        ))
        ## We do now add nodes for the students. Every preference of the
        ## student is an 'arc' from the student-node to the time-node.
        ## We do add the arcs here as well.
        time_preferences = self.lecture.time_preferences
        students = set([tp.student for tp in time_preferences])
        student_nodes = {}
        for student in students:
            nodes.append(StudentNode(
                    student=student,
                    id=student.id,
                    time=None
            ))
            student_nodes[student.id] = len(nodes)-1
            arcs.append(Arc(len(nodes)-1, 1,
                    priority = utils.ghostpenalty,
                    type = 'priority_arc',
                    extra = 'student=>ghost'
                    ))
            student_preferences = [tp for tp in student.time_preferences if tp.lecture_id == self.lecture.id]
            for tp in student_preferences:
                for i,node in enumerate(nodes):
                    if node.type=='time' and node.time and node.time == tp.time:
                        arcs.append(Arc(len(nodes)-1,i,
                                priority=tp.penalty,
                                type='priority_arc',
                                extra='__need_to_be_filled__'
                                ))
                        break
                    elif node.type == 'student':
                        break
        if len(students) == 0:
            return {'error_value': 0,
                    'students_processed': 0}
        # we do now write a file in the popular dimacs format.
        inputfile = "c This is Muesli. \n"
        inputfile += "p min %i %i\n" %(len(nodes), len(arcs))
        for i, node in enumerate(nodes):
            inputfile += 'n %i ' % (i+1)
            if node.type == 'master':
                inputfile += '-%i\n' % (len(students))
            elif node.type == 'time':
                inputfile += '0\n'
            else:
                inputfile += '1\n'
        for i, arc in enumerate(arcs):
            inputfile += 'a %i %i 0 ' % (arc.src+1, arc.dest+1)
            if arc.type == 'times=>master':
                inputfile += '%i 1\n' % arc.priority
            else:
                inputfile += '1 %i\n' % arc.priority

        tmpfile = tempfile.NamedTemporaryFile(prefix='muesli', mode='w')
        tmpfile.write(inputfile)
        tmpfile.flush()
        out, err = subprocess.Popen([utils.lpsolve, '-rxli', 'xli_DIMACS', tmpfile.name], stdout=subprocess.PIPE,
                                    universal_newlines=True).communicate()
        tmpfile.close()
        if 'Successfully' not in out:
            raise Exception('Optimizer Error: File Format wrong')
        out = out.split('Actual values')[1].split('\n', 1)[1]
        lines = out.split('\n')
        if not len(lines)>len(arcs):
            raise Exception('Optimizer Error: File Format wrong')
        lines = reversed(lines)
        self.lecture.lecture_students.delete()
        global_happiness = 0.0
        students_unhappy = []
        students_without_group = []
        narcs = list(arcs)
        arc = narcs.pop()
        for line in lines:
            if line=='': continue
            line = line.split()[1]
            if arc.extra == '__need_to_be_filled__' and line=='1':
                sorted_tutorials = list(nodes[arc.dest].tutorials)
                sorted_tutorials.sort(key=lambda t: t['act_students'])
                ls = models.LectureStudent()
                ls.student = nodes[arc.src].student
                ls.lecture = self.lecture
                ls.tutorial = sorted_tutorials[0]['tutorial']
                self.session.add(ls)
                sorted_tutorials[0]['act_students'] += 1
                if arc.priority >= utils.students_unhappiness:
                    students_unhappy.append(nodes[arc.src].student)
                global_happiness += 1/float(arc.priority)
            elif arc.extra == 'student=>ghost' and line=='1':
                students_without_group.append(nodes[arc.src].student)
            elif arc.type == 'times=>master':
                break
            arc = narcs.pop()
        self.session.commit()
        return {'error_value':0,
                'students_processed': len(students),
                'students_without_group': students_without_group,
                'students_unhappy': students_unhappy,
                'global_happiness': 100.0*global_happiness/(len(students) - len(students_without_group)) if len(students)!=len(students_without_group) else 0
                }

  #my @lines = reverse <OUTFILE>;
  #if ($lines[scalar @lines - 1] =~ m/^Successfully/ && (scalar @lines) > (scalar @arcs)) {
    #$i = scalar @arcs -1;
    #$c->model('MuesliDB')->schema->txn_do(sub {
      #$lecture->lecture_students->delete;
      #foreach $line (@lines) {
        #if ($arcs[$i]{extra} eq '__need_to_be_filled__' && $line =~ m/^1/) {
          #my @sorted = sort { $a->{act_students} <=> $b->{act_students} }
            #@{$nodes[$arcs[$i]{dest}]->{tutorials}};
          #$c->model('MuesliDB::LectureStudents')->create({
            #lecture => $lecture->id,
            #student => $nodes[$arcs[$i]{src}]->{id},
            #tutorial => $sorted[0]->{id},
          #});
          #$sorted[0]->{act_students}++;
          #if ($arcs[$i]{priority} >= $c->config->{students_unhappiness}) {
            #push(@students_unhappy, $nodes[$arcs[$i]{src}]{obj});
          #}
          #$global_happiness += 1/$arcs[$i]{priority};
        #} elsif ($arcs[$i]{extra} eq 'student=>ghost' && $line =~ m/^1/) {
          #push(@students_without_group, $nodes[$arcs[$i]{src}]{obj} );
        #} elsif ($arcs[$i]{type} eq 'times=>master') { last; }
        #$i--;
      #}
    #});
    #$lecture->mode('off');
    #$lecture->update;
    #$result = {
      #err_val => undef,
      #students_processed => $stud_number,
      #students_without_group => \@students_without_group,
      #students_unhappy => \@students_unhappy,
      #global_happiness => 100*$global_happiness / ($stud_number - scalar @students_without_group),
    #};
  #} else {
    #$result = {
      #err_val => 'Optimizer error: File format wrong',
      #students_processed => 0,
    #}
  #}
  #return $result;
#}
