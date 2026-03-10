/**
 * DynamicFormsDesigner — Visual form schema designer.
 *
 * Manages a JSON schema with pages, fields, validators, conditions, and options.
 * Serializes to the hidden input on form submit.
 */
var DynamicFormsDesigner = (function() {
    'use strict';

    var containerId = '';
    var hiddenInputId = '';
    var container = null;

    // State
    var schemaState = {
        pages: []
    };

    var FIELD_TYPES = [
        { value: 'string', label: 'Text' },
        { value: 'number', label: 'Number' },
        { value: 'integer', label: 'Integer' },
        { value: 'boolean', label: 'Boolean (Checkbox)' },
        { value: 'date', label: 'Date' },
        { value: 'file', label: 'File Upload' },
        { value: 'geolocation', label: 'Geolocation' }
    ];

    var CONDITION_OPERATORS = [
        { value: 'equals', label: 'Equals' },
        { value: 'not_equals', label: 'Not Equals' },
        { value: 'contains', label: 'Contains' },
        { value: 'greater_than', label: 'Greater Than' },
        { value: 'less_than', label: 'Less Than' },
        { value: 'between', label: 'Between' }
    ];

    // -----------------------------------------------------------------------
    // Helpers
    // -----------------------------------------------------------------------
    function el(tag, attrs, children) {
        var elem = document.createElement(tag);
        if (attrs) {
            Object.keys(attrs).forEach(function(k) {
                if (k === 'className') elem.className = attrs[k];
                else if (k === 'innerHTML') elem.innerHTML = attrs[k];
                else if (k.startsWith('on')) elem.addEventListener(k.slice(2).toLowerCase(), attrs[k]);
                else elem.setAttribute(k, attrs[k]);
            });
        }
        if (children) {
            if (typeof children === 'string') elem.textContent = children;
            else if (Array.isArray(children)) children.forEach(function(c) { if (c) elem.appendChild(c); });
            else elem.appendChild(children);
        }
        return elem;
    }

    function getAllFieldNames() {
        var names = [];
        schemaState.pages.forEach(function(page) {
            (page.fields || []).forEach(function(f) {
                if (f.name) names.push(f.name);
            });
        });
        return names;
    }

    // -----------------------------------------------------------------------
    // Serialization
    // -----------------------------------------------------------------------
    function serializeToJSON() {
        var json = JSON.stringify({ pages: schemaState.pages });
        var input = document.getElementById(hiddenInputId);
        if (input) input.value = json;
        return json;
    }

    function loadFromJSON(data) {
        if (!data) return;
        if (typeof data === 'string') {
            try { data = JSON.parse(data); } catch(e) { return; }
        }
        schemaState.pages = data.pages || [];
        render();
    }

    // -----------------------------------------------------------------------
    // Page management
    // -----------------------------------------------------------------------
    function addPage() {
        schemaState.pages.push({
            title: 'Page ' + (schemaState.pages.length + 1),
            fields: []
        });
        render();
    }

    function removePage(pageIdx) {
        if (schemaState.pages.length <= 1) {
            alert('You must have at least one page.');
            return;
        }
        if (!confirm('Remove this page and all its fields?')) return;
        schemaState.pages.splice(pageIdx, 1);
        render();
    }

    function movePageUp(pageIdx) {
        if (pageIdx <= 0) return;
        var tmp = schemaState.pages[pageIdx];
        schemaState.pages[pageIdx] = schemaState.pages[pageIdx - 1];
        schemaState.pages[pageIdx - 1] = tmp;
        render();
    }

    function movePageDown(pageIdx) {
        if (pageIdx >= schemaState.pages.length - 1) return;
        var tmp = schemaState.pages[pageIdx];
        schemaState.pages[pageIdx] = schemaState.pages[pageIdx + 1];
        schemaState.pages[pageIdx + 1] = tmp;
        render();
    }

    // -----------------------------------------------------------------------
    // Field management
    // -----------------------------------------------------------------------
    function addField(pageIdx) {
        var fields = schemaState.pages[pageIdx].fields;
        fields.push({
            name: '',
            type: 'string',
            label: '',
            required: false,
            help_text: '',
            order: fields.length,
            validators: {},
            conditions: null
        });
        render();
    }

    function removeField(pageIdx, fieldIdx) {
        schemaState.pages[pageIdx].fields.splice(fieldIdx, 1);
        render();
    }

    function moveFieldUp(pageIdx, fieldIdx) {
        if (fieldIdx <= 0) return;
        var fields = schemaState.pages[pageIdx].fields;
        var tmp = fields[fieldIdx];
        fields[fieldIdx] = fields[fieldIdx - 1];
        fields[fieldIdx - 1] = tmp;
        reorderFields(pageIdx);
        render();
    }

    function moveFieldDown(pageIdx, fieldIdx) {
        var fields = schemaState.pages[pageIdx].fields;
        if (fieldIdx >= fields.length - 1) return;
        var tmp = fields[fieldIdx];
        fields[fieldIdx] = fields[fieldIdx + 1];
        fields[fieldIdx + 1] = tmp;
        reorderFields(pageIdx);
        render();
    }

    function reorderFields(pageIdx) {
        schemaState.pages[pageIdx].fields.forEach(function(f, i) {
            f.order = i;
        });
    }

    // -----------------------------------------------------------------------
    // Rendering
    // -----------------------------------------------------------------------
    function render() {
        if (!container) return;
        container.innerHTML = '';

        // Pages
        schemaState.pages.forEach(function(page, pageIdx) {
            container.appendChild(renderPage(page, pageIdx));
        });

        // Add page button
        container.appendChild(
            el('button', {
                className: 'btn btn-outline-success mt-3 df-add-page-btn',
                type: 'button',
                onClick: function(e) { e.preventDefault(); addPage(); }
            }, '+ Add Page')
        );

        // JSON Preview
        container.appendChild(renderPreview());

        // Update hidden input
        serializeToJSON();
    }

    function renderPage(page, pageIdx) {
        var card = el('div', { className: 'card mb-3 df-page-card' });

        // Header
        var header = el('div', { className: 'card-header d-flex justify-content-between align-items-center' });
        var titleInput = el('input', {
            type: 'text',
            className: 'form-control form-control-sm d-inline-block',
            style: 'width: 200px;',
            value: page.title || ''
        });
        titleInput.addEventListener('input', function() {
            page.title = this.value;
            serializeToJSON();
        });

        var titleLabel = el('span', {}, [
            document.createTextNode('Page ' + (pageIdx + 1) + ': '),
            titleInput
        ]);

        var btnGroup = el('div', { className: 'btn-group btn-group-sm' });
        btnGroup.appendChild(el('button', {
            type: 'button', className: 'btn btn-outline-secondary',
            onClick: function(e) { e.preventDefault(); movePageUp(pageIdx); }
        }, '\u2191'));
        btnGroup.appendChild(el('button', {
            type: 'button', className: 'btn btn-outline-secondary',
            onClick: function(e) { e.preventDefault(); movePageDown(pageIdx); }
        }, '\u2193'));
        btnGroup.appendChild(el('button', {
            type: 'button', className: 'btn btn-outline-danger',
            onClick: function(e) { e.preventDefault(); removePage(pageIdx); }
        }, '\u00D7'));

        header.appendChild(titleLabel);
        header.appendChild(btnGroup);
        card.appendChild(header);

        // Body — fields
        var body = el('div', { className: 'card-body' });

        (page.fields || []).forEach(function(field, fieldIdx) {
            body.appendChild(renderField(field, pageIdx, fieldIdx));
        });

        // Add field button
        body.appendChild(el('button', {
            type: 'button',
            className: 'btn btn-outline-primary btn-sm mt-2',
            onClick: function(e) { e.preventDefault(); addField(pageIdx); }
        }, '+ Add Field'));

        card.appendChild(body);
        return card;
    }

    function renderField(field, pageIdx, fieldIdx) {
        var row = el('div', { className: 'df-field-row border rounded p-2 mb-2' });

        // Top row: name, type, required, move, remove
        var topRow = el('div', { className: 'row g-2 align-items-center mb-2' });

        // Name
        var nameCol = el('div', { className: 'col-md-3' });
        var nameInput = el('input', {
            type: 'text', className: 'form-control form-control-sm',
            placeholder: 'Field name (snake_case)', value: field.name || ''
        });
        nameInput.addEventListener('input', function() {
            field.name = this.value.replace(/[^a-zA-Z0-9_]/g, '_').toLowerCase();
            this.value = field.name;
            serializeToJSON();
        });
        nameCol.appendChild(nameInput);

        // Label
        var labelCol = el('div', { className: 'col-md-3' });
        var labelInput = el('input', {
            type: 'text', className: 'form-control form-control-sm',
            placeholder: 'Label', value: field.label || ''
        });
        labelInput.addEventListener('input', function() {
            field.label = this.value;
            serializeToJSON();
        });
        labelCol.appendChild(labelInput);

        // Type
        var typeCol = el('div', { className: 'col-md-2' });
        var typeSelect = el('select', { className: 'form-select form-select-sm' });
        FIELD_TYPES.forEach(function(ft) {
            var opt = el('option', { value: ft.value }, ft.label);
            if (ft.value === field.type) opt.selected = true;
            typeSelect.appendChild(opt);
        });
        typeSelect.addEventListener('change', function() {
            field.type = this.value;
            field.validators = {};
            delete field.enum;
            delete field.multi;
            render();
        });
        typeCol.appendChild(typeSelect);

        // Required
        var reqCol = el('div', { className: 'col-md-1' });
        var reqCheck = el('input', { type: 'checkbox', className: 'form-check-input' });
        reqCheck.checked = !!field.required;
        reqCheck.addEventListener('change', function() {
            field.required = this.checked;
            serializeToJSON();
        });
        var reqLabel = el('label', { className: 'form-check-label ms-1' }, 'Req');
        reqCol.appendChild(reqCheck);
        reqCol.appendChild(reqLabel);

        // Buttons
        var btnCol = el('div', { className: 'col-md-3 text-end' });
        var fieldBtnGroup = el('div', { className: 'btn-group btn-group-sm' });
        fieldBtnGroup.appendChild(el('button', {
            type: 'button', className: 'btn btn-outline-secondary',
            onClick: function(e) { e.preventDefault(); moveFieldUp(pageIdx, fieldIdx); }
        }, '\u2191'));
        fieldBtnGroup.appendChild(el('button', {
            type: 'button', className: 'btn btn-outline-secondary',
            onClick: function(e) { e.preventDefault(); moveFieldDown(pageIdx, fieldIdx); }
        }, '\u2193'));
        fieldBtnGroup.appendChild(el('button', {
            type: 'button', className: 'btn btn-outline-danger',
            onClick: function(e) { e.preventDefault(); removeField(pageIdx, fieldIdx); }
        }, '\u00D7'));
        btnCol.appendChild(fieldBtnGroup);

        topRow.appendChild(nameCol);
        topRow.appendChild(labelCol);
        topRow.appendChild(typeCol);
        topRow.appendChild(reqCol);
        topRow.appendChild(btnCol);
        row.appendChild(topRow);

        // Help text
        var helpRow = el('div', { className: 'row g-2 mb-2' });
        var helpCol = el('div', { className: 'col-12' });
        var helpInput = el('input', {
            type: 'text', className: 'form-control form-control-sm',
            placeholder: 'Help text (optional)', value: field.help_text || ''
        });
        helpInput.addEventListener('input', function() {
            field.help_text = this.value;
            serializeToJSON();
        });
        helpCol.appendChild(helpInput);
        helpRow.appendChild(helpCol);
        row.appendChild(helpRow);

        // Type-specific validators
        row.appendChild(renderValidators(field));

        // Enum/multi for string type
        if (field.type === 'string') {
            row.appendChild(renderEnumEditor(field));
        }

        // Conditions
        row.appendChild(renderConditions(field, pageIdx, fieldIdx));

        return row;
    }

    function renderValidators(field) {
        var wrapper = el('div', { className: 'df-validators mb-2' });
        var type = field.type;
        var v = field.validators || {};

        if (type === 'string' && !field.enum) {
            wrapper.appendChild(renderValidatorRow('min_length', 'Min Length', v.min_length, field));
            wrapper.appendChild(renderValidatorRow('max_length', 'Max Length', v.max_length, field));
        } else if (type === 'number' || type === 'integer') {
            wrapper.appendChild(renderValidatorRow('min_value', 'Min Value', v.min_value, field));
            wrapper.appendChild(renderValidatorRow('max_value', 'Max Value', v.max_value, field));
        } else if (type === 'date') {
            wrapper.appendChild(renderValidatorRow('min_value', 'Min Date (or "today")', v.min_value, field));
            wrapper.appendChild(renderValidatorRow('max_value', 'Max Date (or "today")', v.max_value, field));
        }

        return wrapper;
    }

    function renderValidatorRow(key, label, value, field) {
        var row = el('div', { className: 'row g-2 mb-1' });
        var labelCol = el('div', { className: 'col-md-3' });
        labelCol.appendChild(el('small', { className: 'text-muted' }, label));
        var inputCol = el('div', { className: 'col-md-3' });
        var input = el('input', {
            type: 'text', className: 'form-control form-control-sm',
            value: value !== undefined && value !== null ? String(value) : ''
        });
        input.addEventListener('input', function() {
            if (!field.validators) field.validators = {};
            var val = this.value.trim();
            if (val === '') {
                delete field.validators[key];
            } else {
                field.validators[key] = val;
            }
            serializeToJSON();
        });
        inputCol.appendChild(input);
        row.appendChild(labelCol);
        row.appendChild(inputCol);
        return row;
    }

    function renderEnumEditor(field) {
        var wrapper = el('div', { className: 'df-enum-editor mb-2' });

        // Toggle enum
        var toggleRow = el('div', { className: 'form-check mb-1' });
        var enumCheck = el('input', { type: 'checkbox', className: 'form-check-input', id: 'enum_toggle_' + field.name });
        enumCheck.checked = !!field.enum;
        enumCheck.addEventListener('change', function() {
            if (this.checked) {
                field.enum = field.enum || ['Option 1'];
            } else {
                delete field.enum;
                delete field.multi;
            }
            render();
        });
        toggleRow.appendChild(enumCheck);
        toggleRow.appendChild(el('label', { className: 'form-check-label', htmlFor: 'enum_toggle_' + field.name }, 'Use dropdown/choices'));
        wrapper.appendChild(toggleRow);

        if (field.enum) {
            // Multi toggle
            var multiRow = el('div', { className: 'form-check mb-1' });
            var multiCheck = el('input', { type: 'checkbox', className: 'form-check-input' });
            multiCheck.checked = !!field.multi;
            multiCheck.addEventListener('change', function() {
                field.multi = this.checked;
                serializeToJSON();
            });
            multiRow.appendChild(multiCheck);
            multiRow.appendChild(el('label', { className: 'form-check-label' }, 'Allow multiple selections'));
            wrapper.appendChild(multiRow);

            // Options list
            field.enum.forEach(function(opt, optIdx) {
                var optRow = el('div', { className: 'input-group input-group-sm mb-1' });
                var optInput = el('input', {
                    type: 'text', className: 'form-control', value: opt
                });
                optInput.addEventListener('input', function() {
                    field.enum[optIdx] = this.value;
                    serializeToJSON();
                });
                optRow.appendChild(optInput);
                optRow.appendChild(el('button', {
                    type: 'button', className: 'btn btn-outline-danger',
                    onClick: function(e) {
                        e.preventDefault();
                        field.enum.splice(optIdx, 1);
                        if (field.enum.length === 0) {
                            delete field.enum;
                            delete field.multi;
                        }
                        render();
                    }
                }, '\u00D7'));
                wrapper.appendChild(optRow);
            });

            wrapper.appendChild(el('button', {
                type: 'button', className: 'btn btn-outline-secondary btn-sm',
                onClick: function(e) {
                    e.preventDefault();
                    field.enum.push('Option ' + (field.enum.length + 1));
                    render();
                }
            }, '+ Add Option'));
        }

        return wrapper;
    }

    function renderConditions(field, pageIdx, fieldIdx) {
        var wrapper = el('div', { className: 'df-conditions mt-2' });
        var conditions = field.conditions || { logic: 'AND', rules: [] };

        // Toggle
        var hasConditions = field.conditions && field.conditions.rules && field.conditions.rules.length > 0;
        var toggleBtn = el('button', {
            type: 'button',
            className: 'btn btn-outline-info btn-sm mb-1',
            onClick: function(e) {
                e.preventDefault();
                if (!field.conditions || !field.conditions.rules || field.conditions.rules.length === 0) {
                    field.conditions = { logic: 'AND', rules: [{ field: '', operator: 'equals', value: '' }] };
                } else {
                    field.conditions = null;
                }
                render();
            }
        }, hasConditions ? 'Remove Conditions' : '+ Add Conditions');
        wrapper.appendChild(toggleBtn);

        if (!hasConditions) return wrapper;

        // Logic toggle
        var logicRow = el('div', { className: 'mb-1' });
        var logicSelect = el('select', { className: 'form-select form-select-sm d-inline-block', style: 'width: 100px;' });
        ['AND', 'OR'].forEach(function(l) {
            var opt = el('option', { value: l }, l);
            if (conditions.logic === l) opt.selected = true;
            logicSelect.appendChild(opt);
        });
        logicSelect.addEventListener('change', function() {
            field.conditions.logic = this.value;
            serializeToJSON();
        });
        logicRow.appendChild(el('small', { className: 'text-muted me-1' }, 'Logic: '));
        logicRow.appendChild(logicSelect);
        wrapper.appendChild(logicRow);

        // Rules
        conditions.rules.forEach(function(rule, ruleIdx) {
            wrapper.appendChild(renderConditionRule(field, rule, ruleIdx));
        });

        // Add rule
        wrapper.appendChild(el('button', {
            type: 'button', className: 'btn btn-outline-secondary btn-sm',
            onClick: function(e) {
                e.preventDefault();
                field.conditions.rules.push({ field: '', operator: 'equals', value: '' });
                render();
            }
        }, '+ Add Rule'));

        return wrapper;
    }

    function renderConditionRule(field, rule, ruleIdx) {
        var row = el('div', { className: 'input-group input-group-sm mb-1' });

        // Field selector
        var fieldSelect = el('select', { className: 'form-select' });
        fieldSelect.appendChild(el('option', { value: '' }, '-- Field --'));
        getAllFieldNames().forEach(function(fn) {
            if (fn === field.name) return;
            var opt = el('option', { value: fn }, fn);
            if (rule.field === fn) opt.selected = true;
            fieldSelect.appendChild(opt);
        });
        fieldSelect.addEventListener('change', function() {
            rule.field = this.value;
            serializeToJSON();
        });

        // Operator
        var opSelect = el('select', { className: 'form-select' });
        CONDITION_OPERATORS.forEach(function(op) {
            var opt = el('option', { value: op.value }, op.label);
            if (rule.operator === op.value) opt.selected = true;
            opSelect.appendChild(opt);
        });
        opSelect.addEventListener('change', function() {
            rule.operator = this.value;
            serializeToJSON();
        });

        // Value
        var valueInput = el('input', {
            type: 'text', className: 'form-control',
            placeholder: 'Value', value: rule.value || ''
        });
        valueInput.addEventListener('input', function() {
            rule.value = this.value;
            serializeToJSON();
        });

        // Remove
        var removeBtn = el('button', {
            type: 'button', className: 'btn btn-outline-danger',
            onClick: function(e) {
                e.preventDefault();
                field.conditions.rules.splice(ruleIdx, 1);
                if (field.conditions.rules.length === 0) {
                    field.conditions = null;
                }
                render();
            }
        }, '\u00D7');

        row.appendChild(fieldSelect);
        row.appendChild(opSelect);
        row.appendChild(valueInput);
        row.appendChild(removeBtn);
        return row;
    }

    function renderPreview() {
        var wrapper = el('div', { className: 'df-json-preview mt-4' });
        wrapper.appendChild(el('h6', {}, 'JSON Preview'));
        var pre = el('pre', {
            className: 'border rounded p-2 bg-light',
            style: 'max-height: 300px; overflow-y: auto; font-size: 12px;'
        });
        pre.textContent = JSON.stringify({ pages: schemaState.pages }, null, 2);
        wrapper.appendChild(pre);
        return wrapper;
    }

    // -----------------------------------------------------------------------
    // Init
    // -----------------------------------------------------------------------
    function init(containerElementId, hiddenInputElementId) {
        containerId = containerElementId;
        hiddenInputId = hiddenInputElementId;
        container = document.getElementById(containerId);

        if (!container) {
            console.error('DynamicFormsDesigner: container not found: ' + containerId);
            return;
        }

        // Start with one page if empty
        if (schemaState.pages.length === 0) {
            schemaState.pages.push({ title: 'Page 1', fields: [] });
        }

        render();

        // Hook form submit
        var form = container.closest('form');
        if (form) {
            form.addEventListener('submit', function() {
                serializeToJSON();
            });
        }
    }

    return {
        init: init,
        loadFromJSON: loadFromJSON,
        serializeToJSON: serializeToJSON,
        getState: function() { return schemaState; }
    };
})();
