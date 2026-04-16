import pkgutil

# Compatibility shim for Python 3.14+: some libraries call pkgutil.get_loader
# which was removed in Python 3.14. Provide a minimal replacement using
# importlib to avoid upgrading all dependencies immediately.
if not hasattr(pkgutil, 'get_loader'):
    import importlib.util
    def _compat_get_loader(name):
        try:
            spec = importlib.util.find_spec(name)
            return getattr(spec, 'loader', None) if spec else None
        except Exception:
            return None
    pkgutil.get_loader = _compat_get_loader

from flask import Flask, render_template, request, redirect, url_for, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
try:
    from flask_migrate import Migrate
except Exception:
    Migrate = None
from dateutil.relativedelta import relativedelta
import datetime
import sqlite3
import os
import logging

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'plan.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
if Migrate:
    try:
        migrate = Migrate(app, db)
    except Exception:
        migrate = None
else:
    migrate = None


def _parse_project_date(raw_value):
    if not raw_value:
        return None
    try:
        # Accept full ISO datetimes or plain dates
        return datetime.datetime.fromisoformat(raw_value).date()
    except Exception:
        return None


class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    items = db.relationship('Item', backref='project', cascade='all, delete-orphan')


class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    plans = db.relationship('Plan', backref='item', cascade='all, delete-orphan')


class Plan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    parent_plan_id = db.Column(db.Integer, db.ForeignKey('plan.id'), nullable=True)
    exception_type = db.Column(db.String(20), nullable=True)
    kind = db.Column(db.String(20), default='once')  # 'once' or 'recurring'
    start_dt = db.Column(db.DateTime, nullable=True)
    end_dt = db.Column(db.DateTime, nullable=True)
    freq = db.Column(db.String(20), nullable=True)  # weekly, daily, monthly
    interval = db.Column(db.Integer, default=1)
    weekdays = db.Column(db.String(50), nullable=True)  # e.g. "MO,TU,WE"
    month_day = db.Column(db.Integer, nullable=True)
    all_day = db.Column(db.Boolean, default=False)
    has_time = db.Column(db.Boolean, default=True)
    deleted = db.Column(db.Boolean, default=False)
    completed = db.Column(db.Boolean, default=False)
    note = db.Column(db.String(500), nullable=True)

    def human_readable(self):
        is_all_day = bool(self.all_day) or not bool(getattr(self, 'has_time', True))
        if self.kind == 'once' and self.start_dt:
            if is_all_day:
                return self.start_dt.strftime('%d/%m') + ' Todo el día'
            s = self.start_dt.strftime('%d/%m %H:%M')
            if self.end_dt:
                e = self.end_dt.strftime('%H:%M')
                return f"{s} - {e}"
            return s
        if self.kind == 'recurring' and self.freq:
            parts = []
            if self.freq == 'weekly':
                if self.weekdays:
                    parts.append('Cada ' + ', '.join(self.weekdays.split(',')))
                else:
                    parts.append('Semanal')
            elif self.freq == 'daily':
                # support special daily options stored in weekdays: all/weekdays/weekend
                wd = (self.weekdays or '').lower()
                if wd == 'all' or not wd:
                    parts.append('Diario')
                elif wd == 'weekdays':
                    parts.append('Lunes a viernes')
                elif wd == 'weekend':
                    parts.append('Fines de semana')
                else:
                    parts.append('Diario')
            elif self.freq == 'monthly':
                parts.append('Mensual')
            # add interval in appropriate units
            if self.interval and self.interval > 1:
                unit = 'semanas'
                if self.freq == 'daily':
                    unit = 'días'
                elif self.freq == 'monthly':
                    unit = 'meses'
                parts.append(f'cada {self.interval} {unit}')
            if is_all_day:
                parts.append('Todo el día')
            elif self.start_dt:
                parts.append('a las ' + self.start_dt.strftime('%H:%M'))
            return ' '.join(parts)
        return self.note or ''


def _parse_plan_form(form):
    submitted_kind = form.get('kind', 'once')
    note = form.get('note')
    end_raw = form.get('end_dt')
    freq_from_form = form.get('freq')
    interval = int(form.get('interval') or 1)
    weekdays = form.get('weekdays')
    month_day = form.get('month_day')
    start_dt = None
    end_dt = None
    date_raw = form.get('date')
    time_raw = form.get('time_only')
    all_day_flag = True if form.get('all_day') else False
    has_time_flag = False

    try:
        if date_raw:
            d = datetime.datetime.fromisoformat(date_raw).date()
            if time_raw:
                parts = time_raw.split(':')
                hh = int(parts[0]); mm = int(parts[1])
                start_dt = datetime.datetime.combine(d, datetime.time(hh, mm))
                has_time_flag = True
            else:
                start_dt = datetime.datetime.combine(d, datetime.time(0, 0))
                has_time_flag = False
        else:
            if time_raw:
                parts = time_raw.split(':')
                hh = int(parts[0]); mm = int(parts[1])
                start_dt = datetime.datetime.combine(datetime.date.today(), datetime.time(hh, mm))
                has_time_flag = True
            else:
                has_time_flag = False

        if end_raw:
            if 'T' in end_raw or '-' in end_raw:
                parsed_end = datetime.datetime.fromisoformat(end_raw)
                end_dt = parsed_end if isinstance(parsed_end, datetime.datetime) else datetime.datetime.combine(parsed_end.date(), datetime.time(0, 0))
            else:
                ed = datetime.datetime.fromisoformat(end_raw).date()
                end_dt = datetime.datetime.combine(ed, datetime.time(0, 0))
    except Exception:
        start_dt = None

    if submitted_kind == 'once':
        kind = 'once'
        freq = None
    else:
        kind = 'recurring'
        freq = submitted_kind if submitted_kind in ('daily', 'weekly', 'monthly') else freq_from_form

    error = None
    if submitted_kind == 'once':
        if not date_raw:
            error = 'Para planificaciones puntuales la fecha es obligatoria.'
    else:
        if freq == 'daily':
            if not interval or int(interval) < 1:
                error = 'Para recurrencias diarias el intervalo (días) es obligatorio y debe ser >= 1.'
        elif freq == 'weekly':
            if not interval or int(interval) < 1:
                error = 'Para recurrencias semanales el intervalo (semanas) es obligatorio y debe ser >= 1.'
            if not weekdays:
                error = 'Para recurrencias semanales debes seleccionar un día de la semana.'
        elif freq == 'monthly':
            if not interval or int(interval) < 1:
                error = 'Para recurrencias mensuales el intervalo (meses) es obligatorio y debe ser >= 1.'
            if not month_day:
                error = 'Para recurrencias mensuales debes indicar el día del mes.'

    if not all_day_flag and not time_raw:
        error = 'La hora es obligatoria salvo que marques Todo el día.'

    md = None
    try:
        if month_day:
            md = int(month_day)
    except Exception:
        md = None

    return {
        'kind': kind,
        'freq': freq,
        'note': note,
        'start_dt': start_dt,
        'end_dt': end_dt,
        'interval': interval,
        'weekdays': weekdays,
        'month_day': md,
        'all_day': all_day_flag,
        'has_time': has_time_flag,
        'completed': True if form.get('completed') else False,
        'submitted_kind': submitted_kind,
        'error': error,
    }


@app.route('/')
def index():
    projects = Project.query.order_by(Project.id.desc()).all()
    return render_template('index.html', projects=projects)


@app.route('/project/<int:project_id>/', methods=['GET', 'POST'])
def project_view(project_id):
    project = Project.query.get_or_404(project_id)
    deleted_id = request.args.get('deleted_id')
    if request.method == 'POST':
        if 'project_name' in request.form and 'update_project' in request.form:
            name = request.form.get('project_name', '').strip()
            start_date_raw = request.form.get('start_date')
            end_date_raw = request.form.get('end_date')
            if name:
                project.name = name
            project.start_date = _parse_project_date(start_date_raw)
            project.end_date = _parse_project_date(end_date_raw)
            db.session.add(project)
            db.session.commit()
            return redirect(url_for('project_view', project_id=project_id))
        update_item_id = request.form.get('update_item_id')
        item_name = request.form.get('item_name')
        if update_item_id:
            item = Item.query.get_or_404(int(update_item_id))
            name = (item_name or '').strip()
            if name:
                item.name = name
                db.session.add(item)
                db.session.commit()
                return redirect(url_for('project_view', project_id=project_id, selected_item=item.id))
            return redirect(url_for('project_view', project_id=project_id))
        # add item
        if item_name:
            name = item_name.strip()
            if name:
                it = Item(name=name, project=project)
                db.session.add(it)
                db.session.commit()
                return redirect(url_for('project_view', project_id=project_id, selected_item=it.id))
            return redirect(url_for('project_view', project_id=project_id))
        update_plan_id = request.form.get('update_plan_id')
        plan_item_id = request.form.get('plan_item_id')

        if update_plan_id:
            plan_id = int(update_plan_id)
            item_id = int(request.form.get('selected_item') or 0)
            plan = Plan.query.get_or_404(plan_id)
            parsed = _parse_plan_form(request.form)

            if parsed['error']:
                # if AJAX request, return JSON so modal can show error
                if request.headers.get('X-Requested-With'):
                    return jsonify({'ok': False, 'error': parsed['error']})
                project = Project.query.get_or_404(project_id)
                return render_template('project.html', project=project, form_error=parsed['error'], selected_item=item_id or plan.item_id, today=datetime.date.today())

            plan.kind = parsed['kind']
            plan.start_dt = parsed['start_dt']
            plan.end_dt = parsed['end_dt']
            plan.freq = parsed['freq']
            plan.interval = parsed['interval']
            plan.weekdays = parsed['weekdays']
            plan.month_day = parsed['month_day']
            plan.note = parsed['note']
            plan.all_day = parsed['all_day']
            plan.has_time = parsed['has_time']
            # allow setting completed when editing one-off plans
            plan.completed = bool(parsed.get('completed', False))
            db.session.add(plan)
            db.session.commit()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'ok': True})
            return redirect(url_for('project_view', project_id=project_id, selected_item=item_id or plan.item_id))

        # add plan
        if plan_item_id:
            item_id = int(plan_item_id)
            parsed = _parse_plan_form(request.form)

            if parsed['error']:
                if request.headers.get('X-Requested-With'):
                    return jsonify({'ok': False, 'error': parsed['error']})
                project = Project.query.get_or_404(project_id)
                return render_template('project.html', project=project, form_error=parsed['error'], selected_item=item_id, today=datetime.date.today())

            plan = Plan(
                item_id=item_id,
                kind=parsed['kind'],
                start_dt=parsed['start_dt'],
                end_dt=parsed['end_dt'],
                freq=parsed['freq'],
                interval=parsed['interval'],
                weekdays=parsed['weekdays'],
                month_day=parsed['month_day'],
                note=parsed['note'],
                all_day=parsed['all_day'],
                has_time=parsed['has_time'],
                completed=bool(parsed.get('completed', False)),
            )
            db.session.add(plan)
            db.session.commit()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'ok': True})
            return redirect(url_for('project_view', project_id=project_id, selected_item=item_id))

    selected_item = request.args.get('selected_item')
    return render_template('project.html', project=project, deleted_id=deleted_id, selected_item=selected_item, today=datetime.date.today())


@app.route('/project/<int:project_id>/delete', methods=['POST'])
def delete_project(project_id):
    project = Project.query.get_or_404(project_id)
    db.session.delete(project)
    db.session.commit()
    return redirect(url_for('index'))


@app.route('/item/<int:item_id>/delete', methods=['POST'])
def delete_item(item_id):
    item = Item.query.get_or_404(item_id)
    project_id = item.project_id
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for('project_view', project_id=project_id))


@app.route('/plan/<int:plan_id>/edit', methods=['GET', 'POST'])
def edit_plan(plan_id):
    plan = Plan.query.get_or_404(plan_id)
    item = plan.item
    project = item.project
    if request.method == 'POST':
        parsed = _parse_plan_form(request.form)
        if parsed['error']:
            return render_template('edit_plan.html', project=project, item=item, plan=plan, form_error=parsed['error'])

        plan.kind = parsed['kind']
        plan.start_dt = parsed['start_dt']
        plan.end_dt = parsed['end_dt']
        plan.freq = parsed['freq']
        plan.interval = parsed['interval']
        plan.weekdays = parsed['weekdays']
        plan.month_day = parsed['month_day']
        plan.note = parsed['note']
        plan.all_day = parsed['all_day']
        plan.has_time = parsed['has_time']
        db.session.add(plan)
        db.session.commit()
        return redirect(url_for('project_view', project_id=project.id, selected_item=item.id))

    return render_template('edit_plan.html', project=project, item=item, plan=plan)


def _span_dates_for_view(view, ref_date):
    if view == 'day':
        start = ref_date
        end = ref_date
    elif view == 'month':
        start = ref_date.replace(day=1)
        end = (start + relativedelta(months=1)) - datetime.timedelta(days=1)
    else:  # week
        # week starting Monday
        start = ref_date - datetime.timedelta(days=ref_date.weekday())
        end = start + datetime.timedelta(days=6)
    return start, end


def get_occurrences(start_date, end_date):
    # returns list of dicts: {date: date, time: time or None, item: Item, plan: Plan, note}
    events = []
    spanish_weekdays = {
        'Lunes': 0, 'Martes': 1, 'Miércoles': 2, 'Miercoles': 2, 'Jueves': 3,
        'Viernes': 4, 'Sábado': 5, 'Sabado': 5, 'Domingo': 6
    }
    # base plans (original plans) — exclude plans that are exceptions (have parent_plan_id)
    base_plans = Plan.query.filter(Plan.deleted == False, Plan.parent_plan_id == None).all()
    # exception plans (associated to a parent plan)
    exception_plans = Plan.query.filter(Plan.deleted == False, Plan.parent_plan_id != None).all()

    # build a quick lookup for exceptions by parent_id
    # we'll match exceptions to occurrences according to:
    # - all-day exceptions (has_time False) match by date
    # - timed exceptions (has_time True) match by date AND time
    exceptions_by_parent = {}
    for ex in exception_plans:
        exceptions_by_parent.setdefault(ex.parent_plan_id, []).append(ex)
    def _is_cancelled_by_exception(parent_id, occ_date, occ_time):
        exs = exceptions_by_parent.get(parent_id) or []
        for e in exs:
            if getattr(e, 'exception_type', '') != 'cancel':
                continue
            e_has_time = bool(getattr(e, 'has_time', True))
            if e.start_dt:
                e_date = e.start_dt.date()
                e_time = e.start_dt.time() if e_has_time else None
            else:
                e_date = None
                e_time = None
            if e_has_time:
                if e_date == occ_date and occ_time is not None and e_time == occ_time:
                    return True
            else:
                if e_date == occ_date:
                    return True
        return False
    day_count = (end_date - start_date).days + 1
    date_list = [start_date + datetime.timedelta(days=i) for i in range(day_count)]

    for pl in base_plans:
        # determine if this plan should be considered all-day when no explicit time
        pl_has_time = getattr(pl, 'has_time', True)
        is_all_day = bool(getattr(pl, 'all_day', False)) or (not pl_has_time)
        if pl.kind == 'once' and pl.start_dt:
            d = pl.start_dt.date()
            if start_date <= d <= end_date:
                events.append({'date': d, 'time': (pl.start_dt.time() if (pl.start_dt and pl_has_time) else None), 'item': pl.item, 'plan': pl, 'note': pl.note, 'all_day': is_all_day})
        elif pl.kind == 'recurring':
            freq = (pl.freq or '').lower()
            if freq == 'weekly':
                wdays = [w.strip() for w in (pl.weekdays or '').split(',') if w.strip()]
                wnums = [spanish_weekdays.get(w, None) for w in wdays]
                wnums = [n for n in wnums if n is not None]
                anchor = pl.start_dt.date() if pl.start_dt else None
                for d in date_list:
                    if wnums and d.weekday() in wnums:
                        if pl.interval and pl.interval > 1:
                            if anchor:
                                if d >= anchor:
                                    weeks = (d - anchor).days // 7
                                    if weeks % pl.interval == 0:
                                        events.append({'date': d, 'time': (pl.start_dt.time() if (pl.start_dt and pl_has_time) else None), 'item': pl.item, 'plan': pl, 'note': pl.note, 'all_day': is_all_day})
                            else:
                                # no anchor: try to build an anchor from the weekday and time if present
                                if pl.start_dt and pl.start_dt.time():
                                    # compute next date with that weekday from today
                                    today = datetime.date.today()
                                    target_w = d.weekday()
                                    delta_days = (target_w - today.weekday()) % 7
                                    anchor_guess = today + datetime.timedelta(days=delta_days)
                                    weeks = (d - anchor_guess).days // 7
                                    if weeks % pl.interval == 0:
                                        events.append({'date': d, 'time': (pl.start_dt.time() if (pl.start_dt and pl_has_time) else None), 'item': pl.item, 'plan': pl, 'note': pl.note, 'all_day': is_all_day})
                                else:
                                    # check cancel exceptions matching date/time
                                    occ_time = (pl.start_dt.time() if (pl.start_dt and pl_has_time) else None)
                                    if _is_cancelled_by_exception(pl.id, d, occ_time):
                                        continue
                                    events.append({'date': d, 'time': occ_time, 'item': pl.item, 'plan': pl, 'note': pl.note, 'all_day': is_all_day})
                        else:
                            # simple weekly: check cancel exceptions
                            occ_time = (pl.start_dt.time() if (pl.start_dt and pl_has_time) else None)
                            if _is_cancelled_by_exception(pl.id, d, occ_time):
                                continue
                            events.append({'date': d, 'time': occ_time, 'item': pl.item, 'plan': pl, 'note': pl.note, 'all_day': is_all_day})
            elif freq == 'daily':
                # daily: support special options via pl.weekdays: 'all', 'weekdays', 'weekend'
                wd = (pl.weekdays or '').lower()
                for d in date_list:
                    include = False
                    if wd == 'weekdays':
                        include = d.weekday() < 5
                    elif wd == 'weekend':
                        include = d.weekday() >= 5
                    else:
                                # default 'all' or numeric interval fallback
                                if wd == 'all' or not wd:
                                    include = True
                                elif wd.isdigit():
                                    # numeric interval fallback using anchor
                                    anchor = pl.start_dt.date() if pl.start_dt else None
                                    if pl.interval and pl.interval > 1 and anchor:
                                        if d >= anchor and ((d - anchor).days % pl.interval == 0):
                                            include = True
                                else:
                                    # unexpected string values (e.g. a weekday name stored here)
                                    # treat as 'all' to be permissive so a user-chosen "Diario" shows every day
                                    include = True
                    if include:
                        occ_time = (pl.start_dt.time() if (pl.start_dt and pl_has_time) else None)
                        if _is_cancelled_by_exception(pl.id, d, occ_time):
                            continue
                        events.append({'date': d, 'time': occ_time, 'item': pl.item, 'plan': pl, 'note': pl.note, 'all_day': is_all_day})
            elif freq == 'monthly':
                anchor = pl.start_dt.date() if pl.start_dt else None
                target_day = pl.month_day if getattr(pl, 'month_day', None) else (anchor.day if anchor else None)
                for d in date_list:
                    if target_day and d.day == target_day:
                        if pl.interval and pl.interval > 1:
                            if anchor:
                                months = (d.year - anchor.year) * 12 + (d.month - anchor.month)
                                if d >= anchor and (months % pl.interval == 0):
                                        events.append({'date': d, 'time': pl.start_dt.time() if pl.start_dt else None, 'item': pl.item, 'plan': pl, 'note': pl.note, 'all_day': is_all_day})
                            else:
                                # check cancel exceptions
                                occ_time = pl.start_dt.time() if pl.start_dt else None
                                if _is_cancelled_by_exception(pl.id, d, occ_time):
                                    continue
                                events.append({'date': d, 'time': occ_time, 'item': pl.item, 'plan': pl, 'note': pl.note, 'all_day': bool(getattr(pl, 'all_day', False))})
                        else:
                                events.append({'date': d, 'time': (pl.start_dt.time() if (pl.start_dt and pl_has_time) else None), 'item': pl.item, 'plan': pl, 'note': pl.note, 'all_day': is_all_day})
            else:
                # fallback: if start_dt falls in range, include — also check exceptions
                if pl.start_dt:
                    d = pl.start_dt.date()
                    if start_date <= d <= end_date:
                        occ_time = pl.start_dt.time() if pl.start_dt else None
                        if _is_cancelled_by_exception(pl.id, d, occ_time):
                            continue
                        events.append({'date': d, 'time': occ_time, 'item': pl.item, 'plan': pl, 'note': pl.note, 'all_day': is_all_day})

    # remove base occurrences that have any matching exception (cancel or edit)
    pruned = []
    for e in events:
        parent_id = e['plan'].id
        exs = exceptions_by_parent.get(parent_id) or []
        matched = False
        for ex in exs:
            e_has_time = bool(getattr(ex, 'has_time', True))
            if ex.start_dt:
                ex_date = ex.start_dt.date()
                ex_time = ex.start_dt.time() if e_has_time else None
            else:
                ex_date = None
                ex_time = None
            if e_has_time:
                if ex_date == e['date'] and e['time'] is not None and ex_time == e['time']:
                    matched = True
                    break
            else:
                if ex_date == e['date']:
                    matched = True
                    break
        if not matched:
            pruned.append(e)
    events = pruned

    # remove base occurrences that have any matching exception (cancel or edit)
    matched_exception_ids = set()
    pruned = []
    for e in events:
        parent_id = e['plan'].id
        exs = exceptions_by_parent.get(parent_id) or []
        matched = False
        for ex in exs:
            e_has_time = bool(getattr(ex, 'has_time', True))
            if ex.start_dt:
                ex_date = ex.start_dt.date()
                ex_time = ex.start_dt.time() if e_has_time else None
            else:
                ex_date = None
                ex_time = None
            if e_has_time:
                if ex_date == e['date'] and e['time'] is not None and ex_time == e['time']:
                    matched = True
                    matched_exception_ids.add(ex.id)
                    break
            else:
                if ex_date == e['date']:
                    matched = True
                    matched_exception_ids.add(ex.id)
                    break
        if not matched:
            pruned.append(e)
    events = pruned

    # include exception plans that are not cancellations (e.g., 'extra' or moved occurrences)
    for ex in exception_plans:
        if getattr(ex, 'exception_type', None) == 'cancel':
            continue
        if ex.start_dt:
            d = ex.start_dt.date()
            if start_date <= d <= end_date:
                evento_vinculado = ex.id in matched_exception_ids
                events.append({'date': d, 'time': (ex.start_dt.time() if ex.start_dt and getattr(ex, 'has_time', True) else None), 'item': ex.item, 'plan': ex, 'note': ex.note, 'all_day': bool(getattr(ex, 'all_day', False)), 'evento_vinculado': evento_vinculado})

    # filter events by their project's start/end dates so recurring plans
    # outside the project's active range are not shown
    filtered = []
    for e in events:
        proj = getattr(e['item'], 'project', None)
        if not proj:
            filtered.append(e)
            continue
        ps = getattr(proj, 'start_date', None)
        pe = getattr(proj, 'end_date', None)
        # project dates may be strings (legacy) or date objects
        if isinstance(ps, str):
            try:
                ps = datetime.datetime.fromisoformat(ps).date()
            except Exception:
                ps = None
        if isinstance(pe, str):
            try:
                pe = datetime.datetime.fromisoformat(pe).date()
            except Exception:
                pe = None
        if ps and e['date'] < ps:
            continue
        if pe and e['date'] > pe:
            continue
        filtered.append(e)

    # sort events: date, all-day first, then time
    def _sort_key(e):
        return (e['date'], 0 if e.get('all_day') else 1, e['time'] or datetime.time(0, 0))
    filtered.sort(key=_sort_key)
    return filtered


@app.route('/calendar')
def calendar_view():
    view = request.args.get('view', 'week')
    date_str = request.args.get('date')
    project_id_raw = request.args.get('project_id')
    item_id_raw = request.args.get('item_id')
    target_str = request.args.get('target')
    try:
        parsed_date = datetime.datetime.fromisoformat(date_str).date() if date_str else datetime.date.today()
    except Exception:
        parsed_date = datetime.date.today()

    # parse optional 'target' (the user-selected day we want to keep across view changes)
    try:
        target_date = datetime.datetime.fromisoformat(target_str).date() if target_str else None
    except Exception:
        target_date = None

    # Decide the effective reference date depending on whether the target falls
    # within the span of the requested view. If it doesn't, the ref_date becomes
    # the start of the block (first day of week/month as appropriate).
    # Start by computing the tentative span based on the parsed_date.
    tentative_start, tentative_end = _span_dates_for_view(view, parsed_date)

    if target_date:
        if tentative_start <= target_date <= tentative_end:
            ref_date = target_date
        else:
            ref_date = tentative_start
    else:
        ref_date = parsed_date
    start, end = _span_dates_for_view(view, ref_date)
    events = get_occurrences(start, end)

    # optional filtering by project/item
    selected_project_id = None
    selected_item_id = None
    try:
        if project_id_raw:
            selected_project_id = int(project_id_raw)
    except Exception:
        selected_project_id = None
    try:
        if item_id_raw:
            selected_item_id = int(item_id_raw)
    except Exception:
        selected_item_id = None
    if selected_project_id:
        events = [e for e in events if getattr(getattr(e.get('item', None), 'project', None), 'id', None) == selected_project_id]
    if selected_item_id:
        events = [e for e in events if getattr(e.get('item', None), 'id', None) == selected_item_id]

    # provide project list to template for filter UI
    projects = Project.query.order_by(Project.name).all()

    # group by date
    grouped = {}
    d = start
    while d <= end:
        grouped[d] = []
        d += datetime.timedelta(days=1)
    for ev in events:
        grouped.setdefault(ev['date'], []).append(ev)

    # navigation dates
    if view == 'day':
        prev_date = ref_date - datetime.timedelta(days=1)
        next_date = ref_date + datetime.timedelta(days=1)
    elif view == 'month':
        prev_date = (ref_date.replace(day=1) - datetime.timedelta(days=1)).replace(day=1)
        next_date = (ref_date.replace(day=1) + relativedelta(months=1)).replace(day=1)
    else:
        prev_date = ref_date - datetime.timedelta(weeks=1)
        next_date = ref_date + datetime.timedelta(weeks=1)

    return render_template('calendar.html', view=view, ref_date=ref_date, start=start, end=end, grouped=grouped, prev_date=prev_date, next_date=next_date, today=datetime.date.today(), projects=projects, selected_project_id=selected_project_id, selected_item_id=selected_item_id)


@app.route('/api/events')
def api_events():
    # Returns JSON list of occurrences between `start` and `end` (ISO dates).
    start_raw = request.args.get('start')
    end_raw = request.args.get('end')
    try:
        if start_raw:
            start_date = datetime.datetime.fromisoformat(start_raw).date()
        else:
            today = datetime.date.today()
            start_date = today - datetime.timedelta(days=today.weekday())
    except Exception:
        start_date = datetime.date.today() - datetime.timedelta(days=datetime.date.today().weekday())
    try:
        if end_raw:
            end_date = datetime.datetime.fromisoformat(end_raw).date()
        else:
            end_date = start_date + datetime.timedelta(days=13)  # two weeks (current + next)
    except Exception:
        end_date = start_date + datetime.timedelta(days=13)

    occurrences = get_occurrences(start_date, end_date)

    def _serialize(e):
        itm = e.get('item')
        proj = getattr(itm, 'project', None) if itm else None
        return {
            'date': e['date'].isoformat(),
            'time': e['time'].strftime('%H:%M') if e.get('time') else None,
            'all_day': bool(e.get('all_day', False)),
            'item_id': getattr(itm, 'id', None),
            'item_name': getattr(itm, 'name', None),
            'project_id': getattr(proj, 'id', None),
            'project_name': getattr(proj, 'name', None),
            'plan_id': getattr(e.get('plan'), 'id', None),
            'note': e.get('note') or ''
        }

    return jsonify({'ok': True, 'start': start_date.isoformat(), 'end': end_date.isoformat(), 'events': [_serialize(x) for x in occurrences]})


@app.route('/plan/<int:plan_id>/exception', methods=['POST'])
def create_plan_exception(plan_id):
    pl = Plan.query.get_or_404(plan_id)
    # only allow creating exception for base (recurring) plans
    if pl.kind == 'once' or pl.parent_plan_id:
        return jsonify({'ok': False, 'error': 'No es posible crear excepción para este plan.'}), 400

    data = None
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form

    date_raw = data.get('date')
    time_raw = data.get('time')
    ex_type = data.get('type') or 'cancel'
    if not date_raw:
        return jsonify({'ok': False, 'error': 'Falta la fecha.'}), 400
    try:
        ex_date = datetime.datetime.fromisoformat(date_raw).date()
    except Exception:
        return jsonify({'ok': False, 'error': 'Fecha inválida.'}), 400

    ex_time = None
    if time_raw:
        try:
            parts = time_raw.split(':')
            ex_time = datetime.time(int(parts[0]), int(parts[1]))
        except Exception:
            ex_time = None

    # build start_dt for exception plan
    if ex_time:
        start_dt = datetime.datetime.combine(ex_date, ex_time)
        has_time = True
    else:
        start_dt = datetime.datetime.combine(ex_date, datetime.time(0, 0))
        has_time = False

    # prefer provided note when present
    provided_note = (data.get('note') or '').strip() if isinstance(data, dict) else ''
    note_val = provided_note if provided_note else f'Excepción ({ex_type}) de {pl.id}'

    # If this is an edit exception, server may need to create a cancel for the
    # original occurrence (when date/time changed), or remove a cancel that
    # conflicts with the new edit (to avoid duplicates).
    orig_date_raw = data.get('original_date') if isinstance(data, dict) else None
    orig_time_raw = data.get('original_time') if isinstance(data, dict) else None
    orig_dt = None
    if orig_date_raw:
        try:
            od = datetime.datetime.fromisoformat(orig_date_raw).date()
            if orig_time_raw:
                parts = orig_time_raw.split(':')
                ot = datetime.time(int(parts[0]), int(parts[1]))
                orig_dt = datetime.datetime.combine(od, ot)
            else:
                orig_dt = datetime.datetime.combine(od, datetime.time(0, 0))
        except Exception:
            orig_dt = None

    # If creating an edit exception, remove any cancel that matches the new start_dt
    if ex_type == 'edit':
        # remove cancel that matches the new start_dt (if any)
        try:
            q = Plan.query.filter(Plan.parent_plan_id == pl.id, Plan.exception_type == 'cancel')
            # compare by exact datetime if has_time, else by date
            for c in q.all():
                if c.start_dt:
                    if has_time and c.start_dt == start_dt:
                        db.session.delete(c)
                    elif (not has_time) and c.start_dt.date() == start_dt.date():
                        db.session.delete(c)
            db.session.commit()
        except Exception:
            db.session.rollback()

    # create the edit/extra exception
    ex_plan = Plan(
        item_id=pl.item_id,
        parent_plan_id=pl.id,
        exception_type=ex_type,
        kind='once',
        start_dt=start_dt,
        all_day=(not has_time),
        has_time=has_time,
        note=note_val
    )
    db.session.add(ex_plan)
    db.session.commit()

    # If this was an edit that changed date/time from the original occurrence,
    # create a cancel exception at the original datetime so the original
    # occurrence is suppressed.
    if ex_type == 'edit' and orig_dt and orig_dt != start_dt:
        try:
            # check whether such cancel already exists
            exists = Plan.query.filter(Plan.parent_plan_id == pl.id, Plan.exception_type == 'cancel', Plan.start_dt == orig_dt).first()
            if not exists:
                cancel_plan = Plan(
                    item_id=pl.item_id,
                    parent_plan_id=pl.id,
                    exception_type='cancel',
                    kind='once',
                    start_dt=orig_dt,
                    all_day=(not bool(getattr(pl, 'has_time', True))),
                    has_time=bool(getattr(pl, 'has_time', True)),
                    note=f'Cancelación auto por edición de {ex_plan.id}'
                )
                db.session.add(cancel_plan)
                db.session.commit()
        except Exception:
            db.session.rollback()

    return jsonify({'ok': True, 'exception_id': ex_plan.id})


@app.route('/plan/<int:plan_id>/exceptions', methods=['GET'])
def list_plan_exceptions(plan_id):
    pl = Plan.query.get_or_404(plan_id)
    exs = Plan.query.filter(Plan.parent_plan_id == plan_id, Plan.deleted == False).order_by(Plan.start_dt.asc()).all()
    modified = []
    deleted = []
    for ex in exs:
        d = None
        t = None
        if ex.start_dt:
            d = ex.start_dt.date().isoformat()
            if getattr(ex, 'has_time', True) and ex.start_dt.time():
                t = ex.start_dt.time().strftime('%H:%M')
        item = ex.item
        modified_entry = {'id': ex.id, 'start_dt': ex.start_dt.isoformat() if ex.start_dt else None, 'start_dt_date': d, 'time': t, 'note': ex.note or '', 'item_id': item.id if item else None, 'project_id': item.project.id if item and item.project else None, 'parent_plan_id': ex.parent_plan_id}
        if getattr(ex, 'exception_type', None) == 'cancel':
            deleted.append(modified_entry)
        else:
            modified.append(modified_entry)
    return jsonify({'ok': True, 'modified': modified, 'deleted': deleted})


@app.route('/exception/<int:ex_id>/restore', methods=['POST'])
def restore_exception(ex_id):
    ex = Plan.query.get_or_404(ex_id)
    # only restore cancellation exceptions by removing them
    if getattr(ex, 'exception_type', None) != 'cancel':
        return jsonify({'ok': False, 'error': 'Sólo se pueden restaurar excepciones de tipo cancel.'}), 400
    parent_id = ex.parent_plan_id
    try:
        db.session.delete(ex)
        db.session.commit()
        return jsonify({'ok': True, 'parent': parent_id})
    except Exception:
        db.session.rollback()
        return jsonify({'ok': False, 'error': 'Error eliminando excepción'}), 500


@app.route('/exception/<int:ex_id>/get')
def get_exception(ex_id):
    ex = Plan.query.get_or_404(ex_id)
    item = ex.item
    d = None; t = None
    if ex.start_dt:
        d = ex.start_dt.date().isoformat()
        if getattr(ex, 'has_time', True) and ex.start_dt.time():
            t = ex.start_dt.time().strftime('%H:%M')
    return jsonify({'ok': True, 'exception': {'id': ex.id, 'start_dt': ex.start_dt.isoformat() if ex.start_dt else None, 'start_dt_date': d, 'start_dt_time': t, 'note': ex.note or '', 'item_id': item.id if item else None, 'item_name': item.name if item else '', 'project_id': item.project.id if item and item.project else None, 'parent_plan_id': ex.parent_plan_id}})


@app.route('/exception/<int:ex_id>/edit', methods=['POST'])
def edit_exception(ex_id):
    ex = Plan.query.get_or_404(ex_id)
    # only allow editing exceptions (parent_plan_id not null)
    if not ex.parent_plan_id:
        return jsonify({'ok': False, 'error': 'No es una excepción editable.'}), 400
    # parse date/time/note
    data = request.form if not request.is_json else request.get_json()
    date_raw = data.get('date') or data.get('date')
    time_raw = data.get('time') or data.get('time')
    note = (data.get('note') or '').strip() if isinstance(data, dict) else request.form.get('note')
    if not date_raw:
        return jsonify({'ok': False, 'error': 'Falta la fecha.'}), 400
    try:
        ex_date = datetime.datetime.fromisoformat(date_raw).date()
    except Exception:
        return jsonify({'ok': False, 'error': 'Fecha inválida.'}), 400
    ex_time = None
    has_time = False
    if time_raw:
        try:
            parts = time_raw.split(':')
            ex_time = datetime.time(int(parts[0]), int(parts[1]))
            has_time = True
        except Exception:
            ex_time = None
            has_time = False
    if ex_time:
        ex.start_dt = datetime.datetime.combine(ex_date, ex_time)
        ex.has_time = True
        ex.all_day = False
    else:
        ex.start_dt = datetime.datetime.combine(ex_date, datetime.time(0, 0))
        ex.has_time = False
        ex.all_day = True
    ex.note = note
    try:
        db.session.add(ex)
        db.session.commit()
        return jsonify({'ok': True, 'exception_id': ex.id})
    except Exception:
        db.session.rollback()
        return jsonify({'ok': False, 'error': 'Error guardando excepción'}), 500


@app.route('/add_project', methods=['POST'])
def add_project():
    name = request.form.get('project_name')
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    if name:
        sd = None
        pd = None
        if start_date:
            try:
                sd = datetime.datetime.fromisoformat(start_date).date()
            except Exception:
                sd = None
        if end_date:
            try:
                pd = datetime.datetime.fromisoformat(end_date).date()
            except Exception:
                pd = None
        p = Project(name=name.strip(), start_date=sd, end_date=pd)
        db.session.add(p)
        db.session.commit()
    return redirect(url_for('index'))


@app.route('/plan/<int:plan_id>/delete', methods=['POST'])
def delete_plan(plan_id):
    pl = Plan.query.get_or_404(plan_id)
    proj_id = pl.item.project.id if pl.item and pl.item.project else None
    selected_item = request.form.get('selected_item') or (pl.item.id if pl.item else None)
    # soft-delete: mark deleted flag so it's recoverable
    pl.deleted = True
    db.session.add(pl)
    db.session.commit()
    if proj_id:
        return redirect(url_for('project_view', project_id=proj_id, deleted_id=plan_id, selected_item=selected_item))
    return redirect(url_for('index'))


@app.route('/plan/<int:plan_id>/toggle_completed', methods=['POST'])
def toggle_plan_completed(plan_id):
    pl = Plan.query.get_or_404(plan_id)
    # only allow toggle for one-off plans (puntual)
    pl.completed = not bool(getattr(pl, 'completed', False))
    db.session.add(pl)
    db.session.commit()
    # if request is XHR, return simple JSON
    try:
        from flask import jsonify
        return jsonify({'ok': True, 'completed': pl.completed})
    except Exception:
        proj_id = pl.item.project.id if pl.item and pl.item.project else None
        if proj_id:
            return redirect(url_for('project_view', project_id=proj_id))
        return redirect(url_for('index'))


@app.route('/plan/<int:plan_id>/undelete', methods=['POST'])
def undelete_plan(plan_id):
    pl = Plan.query.get_or_404(plan_id)
    proj_id = pl.item.project.id if pl.item and pl.item.project else None
    pl.deleted = False
    db.session.add(pl)
    db.session.commit()
    if proj_id:
        return redirect(url_for('project_view', project_id=proj_id))
    return redirect(url_for('index'))


def init_db():
    db_file = os.path.join(BASE_DIR, 'plan.db')
    with app.app_context():
        if not os.path.exists(db_file):
            db.create_all()
            # Seed with the user's example
            p1 = Project(name='Sesiones Marta')
            it1 = Item(name='Sesión Sergio', project=p1)
            pl1 = Plan(item=it1, kind='recurring', freq='weekly', interval=1, weekdays='Miércoles', start_dt=datetime.datetime.combine(datetime.date.today(), datetime.time(16,0)), end_dt=datetime.datetime.combine(datetime.date.today(), datetime.time(16,30)), note='Todos los miércoles 16:00-16:30')
            it2 = Item(name='Sesión Laura', project=p1)
            pl2 = Plan(item=it2, kind='recurring', freq='weekly', interval=1, weekdays='Viernes', start_dt=datetime.datetime.combine(datetime.date.today(), datetime.time(19,30)), end_dt=datetime.datetime.combine(datetime.date.today(), datetime.time(20,30)), note='Todos los viernes 19:30-20:30')

            p2 = Project(name='Gestiones Laura')
            it3 = Item(name='Recoger a Laura del cole', project=p2)
            # Add several recurring plans as examples
            days = [
                ('Lunes', 17, 0, 'Traerla a casa.'),
                ('Martes', 15, 30, 'Dejarla a las 16:30 en la Iglesia.'),
                ('Miércoles', 15, 15, 'Llevarla a la sesión de Marta a las 16:00.'),
                ('Jueves', 17, 0, 'Traerla a casa.'),
                ('Viernes', 18, 0, 'Merienda en el parque y llevarla a la sesión de Marta.'),
            ]
            for dname, hh, mm, note in days:
                Plan(item=it3, kind='recurring', freq='weekly', interval=1, weekdays=dname, start_dt=datetime.datetime.combine(datetime.date.today(), datetime.time(hh, mm)), note=note)

            it4 = Item(name='Comunión de Laura', project=p2)
            # Quincenal starting 26/04 -> store as recurring every 2 weeks
            try:
                start_comm = datetime.datetime.fromisoformat(f'{datetime.date.today().year}-04-26T10:00')
            except Exception:
                start_comm = datetime.datetime.now()
            Plan(item=it4, kind='recurring', freq='weekly', interval=2, weekdays='Domingo', start_dt=start_comm, note='Quincenal, cada 2 domingos, comenzando el 26/04')
            # One-off final communion day
            try:
                final_dt = datetime.datetime.fromisoformat(f'{datetime.date.today().year}-05-23T10:00')
            except Exception:
                final_dt = datetime.datetime.now()
            Plan(item=it4, kind='once', start_dt=final_dt, note='El día de la Comunión')

            db.session.add_all([p1, p2])
            db.session.commit()

        # ensure DB schema has required columns (lightweight migration)
        try:
            conn = sqlite3.connect(db_file)
            cur = conn.cursor()
            cur.execute("PRAGMA table_info('plan')")
            cols = [r[1] for r in cur.fetchall()]
            if 'month_day' not in cols:
                cur.execute('ALTER TABLE plan ADD COLUMN month_day INTEGER')
                conn.commit()
            if 'all_day' not in cols:
                cur.execute("ALTER TABLE plan ADD COLUMN all_day BOOLEAN DEFAULT 0")
                conn.commit()
            if 'deleted' not in cols:
                cur.execute("ALTER TABLE plan ADD COLUMN deleted BOOLEAN DEFAULT 0")
                conn.commit()
            if 'has_time' not in cols:
                cur.execute("ALTER TABLE plan ADD COLUMN has_time BOOLEAN DEFAULT 1")
                conn.commit()
            if 'completed' not in cols:
                cur.execute("ALTER TABLE plan ADD COLUMN completed BOOLEAN DEFAULT 0")
                conn.commit()
            if 'parent_plan_id' not in cols:
                cur.execute('ALTER TABLE plan ADD COLUMN parent_plan_id INTEGER')
                conn.commit()
            if 'exception_type' not in cols:
                cur.execute("ALTER TABLE plan ADD COLUMN exception_type TEXT")
                conn.commit()
            # ensure project table has new columns (lightweight migration)
            cur.execute("PRAGMA table_info('project')")
            pcols = [r[1] for r in cur.fetchall()]
            if 'start_date' not in pcols:
                cur.execute("ALTER TABLE project ADD COLUMN start_date TEXT")
                conn.commit()
            if 'end_date' not in pcols:
                cur.execute("ALTER TABLE project ADD COLUMN end_date TEXT")
                conn.commit()
            conn.close()
        except Exception:
            # if migration fails, ignore and let ORM raise errors later
            pass


if __name__ == '__main__':
    init_db()
    # Ensure the running Flask process writes its own PID to .flask_pid
    pid_file = os.path.join(BASE_DIR, '.flask_pid')
    log_file = os.path.join(BASE_DIR, 'plan.log')
    # configure simple file logger
    logger = logging.getLogger('plan')
    logger.setLevel(logging.INFO)
    try:
        fh = logging.FileHandler(log_file, encoding='utf-8')
        fh.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))
        logger.addHandler(fh)
    except Exception:
        # if logger can't be configured, fall back to basicConfig
        logging.basicConfig(level=logging.INFO)
    def _write_pid():
        try:
            with open(pid_file, 'w') as fh:
                fh.write(str(os.getpid()))
            logger.info('Wrote PID %s to %s', os.getpid(), pid_file)
            # verify
            if os.path.exists(pid_file):
                try:
                    content = open(pid_file, 'r', encoding='utf-8').read().strip()
                    logger.info('.flask_pid content: %s', content)
                    logger.info('.flask_pid created successfully')
                except Exception as e:
                    logger.error('Failed to read back .flask_pid: %s', e)
            else:
                logger.error('.flask_pid does not exist after write attempt')
        except Exception:
            logger.exception('Failed to write .flask_pid')

    def _remove_pid():
        try:
            if os.path.exists(pid_file):
                os.remove(pid_file)
                logger.info('Removed %s', pid_file)
        except Exception:
            logger.exception('Failed to remove .flask_pid')

    # register cleanup
    try:
        import atexit, signal
        atexit.register(_remove_pid)
        # best-effort signal handlers to remove pid on termination
        try:
            signal.signal(signal.SIGTERM, lambda s, f: (_remove_pid(), os._exit(0)))
        except Exception:
            pass
        try:
            signal.signal(signal.SIGINT, lambda s, f: (_remove_pid(), os._exit(0)))
        except Exception:
            pass
    except Exception:
        pass

    # When running with the Flask reloader (debug=True) the process is
    # started twice (parent + child). Only write the PID from the child
    # process (the one actually serving requests). Werkzeug sets
    # WERKZEUG_RUN_MAIN in the child process.
    if not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        try:
            logger.info('Application starting, pid=%s', os.getpid())
        except Exception:
            pass
        _write_pid()


@app.route('/favicon.ico')
def favicon_route():
    static_dir = os.path.join(BASE_DIR, 'static')
    return send_from_directory(static_dir, 'favicon.ico')

# actually run the app when executed as a script (keep logging on exit)
if __name__ == '__main__':
    # init_db() already called above in the original entry; ensure PID written
    # and then run the Flask development server. Wrap in try/finally so we
    # can log when the process exits and remove the pid file via atexit.
    try:
        try:
            logger.info('Application starting, pid=%s', os.getpid())
        except Exception:
            pass
        try:
            app.run(debug=True)
        finally:
            try:
                logger.info('Application exiting, pid=%s', os.getpid())
            except Exception:
                pass
    except Exception:
        # if the server fails synchronously, log and re-raise
        try:
            logger.exception('Fatal error running application')
        except Exception:
            pass
        raise

