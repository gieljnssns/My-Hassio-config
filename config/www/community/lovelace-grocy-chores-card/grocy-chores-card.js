import {html, LitElement, nothing} from "https://unpkg.com/lit?module";
import {DateTime} from "https://unpkg.com/luxon@3.0.3?module";
import style from './style.js';

class GrocyChoresCard extends LitElement {
    static get styles() {
        return style;
    }

    set hass(hass) {
        let allItems = [];
        this._hass = hass;
        this.entities = [];
        if (Array.isArray(this.config.entity)) {
            for (let i = 0; i < this.config.entity.length; ++i) {
                this.entities[i] = this.config.entity[i] in hass.states ? hass.states[this.config.entity[i]] : null;
            }
        } else {
            this.entities[0] = this.config.entity in hass.states ? hass.states[this.config.entity] : null;
        }

        this.header = this.config.title == null ? "Todo" : this.config.title;

        this._configSetup();

        if (!Array.isArray(this.entities)) {
            return;
        }

        for (let i = 0; i < this.entities.length; i++) {
            let entity = this.entities[i];
            let items;

            if (entity.state === 'unknown') {
                console.warn("The Grocy sensor " + entity.entity_id + " is unknown.");
                continue;
            }

            items = this._getTasks(entity);
            if (items == null) {
                items = this._getChores(entity);
                if (items == null) continue;
            }

            allItems.push(items);
        }

        if (allItems.length === 0) {
            return;
        }

        allItems = allItems.flat(1).filter(function (x) {
            return x !== undefined;
        });

        allItems.sort(function (a, b) {
            if (a.__due_date == null) {
                return -1;
            } else if (b.__due_date == null) {
                return 1;
            }

            return a.__due_date - b.__due_date;
        });

        this.itemsNotVisible = 0;
        this.overflow = [];
        if (this.show_quantity != null) {
            this.items = allItems.slice(0, this.show_quantity);
            if (this.show_overflow) {
                this.overflow = allItems.slice(this.show_quantity);
            } else {
                this.itemsNotVisible = allItems.length - this.items.length;
            }
        } else {
            this.items = allItems;
        }

        this.requestUpdate();
    }

    static getStubConfig() {
        return {
            entity: ["sensor.grocy_chores", "sensor.grocy_tasks"],
            title: "Todo",
            show_quantity: 5,
            show_assigned: true,
            show_overflow: true,
            show_chores_without_due: true,
            show_tasks_without_due: true,
            use_icons: true,
            use_long_date: true,
            due_in_days_threshold: 7,
            use_24_hours: true,
            hide_text_with_no_data: true,
        }
    }

    static getConfigElement() {
        return document.createElement("content-card-editor");
    }

    setConfig(config) {
        if (!config.entity) {
            throw new Error('Please define entity');
        }
        this.config = config;
    }

    render() {
        if (!this.entities) {
            return this._renderEntityNotFound();
        }

        if (this.items === undefined) {
            this.items = [];
            this.overflow = [];
            this.itemsNotVisible = 0;
        }

        if (this.items.length < 1 && !this.show_empty) {
            return;
        }

        return html`
            ${html`
                <ha-card>
                    <h1 class="card-header flex">
                        <div class="name">
                            ${this.header}
                        </div>
                        ${this.show_create_task ? this._renderAddTaskButton() : nothing}
                    </h1>
                    ${this.show_create_task ? this._renderAddTask() : nothing}
                    <div class="card-content">
                        ${this._renderItems(this.items)}
                    </div>
                    ${this.itemsNotVisible > 0 ? this._renderNrItemsInGrocy() : nothing}
                    ${this.overflow && this.overflow.length > 0 ? this._renderOverflow() : nothing}
                </ha-card>`}
        `;
    }

    _renderOverflow() {
        return html`
            <div class="name more-items-title show-class">
                <div>
                    <ha-button class="expand-button show-more-button"
                               @click=${() => this._toggleOverflow(this.renderRoot)}>
                        <div slot="icon" style="width: 100%;">
                            <span class="mdc-button__label">${this._translate(`${this.overflow.length} More Items`)}</span>
                        </div>
                        <div slot="trailingIcon">
                            <ha-icon slot="trailingIcon" style="--mdc-icon-size: ${this.expand_icon_size}px;"
                                     .icon=${"mdi:chevron-down"}></ha-icon>
                        </div>
                    </ha-button>
                </div>
            </div>

            <div class="card-content card-overflow-content hidden-class">
                ${this._renderItems(this.overflow)}
            </div>

            <div class="name more-items-title hidden-class">
                <div>
                    <ha-button class="expand-button show-more-button"
                               @click=${() => this._toggleOverflow(this.renderRoot)}>
                        <div slot="icon" style="width: 100%;">
                            <span class="mdc-button__label">${this._translate("Show Less")}</span>
                        </div>
                        <div slot="trailingIcon">
                            <ha-icon slot="trailingIcon"
                                     .icon=${"mdi:chevron-up"}></ha-icon>
                        </div>
                    </ha-button>
                </div>
            </div>
        `
    }

    _renderItems(cardCollection) {
        if (cardCollection && cardCollection.length > 0) {
            return html`
                ${cardCollection.map(item => this._renderItem(item))}
            `
        } else {
            return html`
                <div class="info flex">${this._translate("No todos")}!</div>
            `
        }
    }

    _renderItem(item) {
        return html`
            <div class="${this.show_divider ? "grocy-item-container" : "grocy-item-container-no-border"} ${this.local_cached_hidden_items.includes(`${item.__type}${item.id}`) ? "hidden-class" : "show-class"} info flex" id="${item.__type}${item.id}">
                <div>
                    ${this._renderItemName(item)}
                    ${this._shouldRenderDueInDays(item) ? this._renderDueInDays(item) : nothing}
                    ${this._shouldRenderAssignedToUser(item) ? this._renderAssignedToUser(item) : nothing}
                    ${this._shouldRenderLastTracked(item) ? this._renderLastTracked(item) : nothing}
                </div>
                ${this.show_track_button && item.__type === "chore" ? this._renderTrackChoreButton(item) : nothing}
                ${this.show_track_button && item.__type === "task" ? this._renderTrackTaskButton(item) : nothing}
            </div>
        `
    }

    _renderEntityNotFound() {
        return html`
            <hui-warning>
                ${this._hass.localize("ui.panel.lovelace.warning.entity_not_found", "entity", this.config.entity)}
            </hui-warning>
        `
    }

    _renderNrItemsInGrocy() {
        return html`
            <div class="secondary not-showing">
                ${this._translate(`Look in Grocy for ${this.itemsNotVisible} more items`)}
            </div>
        `
    }

    _shouldRenderAssignedToUser(item) {
        return this.show_assigned && item.next_execution_assigned_user != null;
    }

    _renderAssignedToUser(item) {
        return html`
            <div class="secondary">
                ${this._translate("Assigned to")}:
                ${item.next_execution_assigned_user.display_name}
            </div>
        `
    }

    _shouldRenderLastTracked(item) {
        return this.show_last_tracked && item.__type === "chore" && (!this.hide_text_with_no_data || item.__last_tracked_date != null);
    }

    _renderLastTracked(item) {
        return html`
            <div class="secondary">
                ${this._translate("Last tracked")}:
                ${this._formatLastTrackedDate(item.__last_tracked_date, item.__last_tracked_days, item.track_date_only) ?? "-"}
                ${this.show_last_tracked_by && item.last_done_by != null ? this._translate("by") + " " + item.last_done_by.display_name : nothing}
            </div>
        `
    }

    _shouldRenderDueInDays(item) {
        return !this.hide_text_with_no_data || item.__due_date != null;
    }

    _renderDueInDays(item) {
        return html`
            <div class="secondary">
                ${this._translate("Due")}:
                <span class=${this._dueHtmlClass(item.__due_in_days) ?? nothing}>${this._formatDueDate(item.__due_date, item.__due_in_days) ?? "-"}</span>
            </div>
        `
    }

    _renderItemName(item) {
        return html`
            <div class="primary">
                ${item.__filtered_name ?? item.name}
            </div>
        `
    }

    _renderAddTaskButton() {
        return html`
            <mwc-button class="hide-button" @click=${() => this._toggleAddTask()}>
                <ha-icon icon="mdi:chevron-down" id="add-task-icon"></ha-icon>
                ${this._translate("Add task")}
            </mwc-button>
        `
    }

    _renderAddTask() {
        return html`
            <div style="display: none;" id="add-task-row" class="add-row">
                <mwc-button @click=${() => this._addTask()}>
                    <ha-icon class="add-icon" icon="mdi:plus"></ha-icon>
                </mwc-button>
                <paper-input
                        id="add-task"
                        class="add-input"
                        no-label-float
                        placeholder=${this._translate("Add task")}>
                </paper-input>
                <paper-input
                        id="add-date"
                        class="add-input"
                        no-label-float
                        placeholder=${this._translate("Optional due date")}
                        value="${this._taskDueDateInputFormat()}">
                </paper-input>
            </div>
        `
    }

    _renderTrackChoreButton(item) {
        if (this.chore_icon != null) {
            return html`
                <mwc-icon-button class="track-button"
                                 .label=${this._translate("Track")}
                                 @click=${() => this._trackChore(item.id, item.name)}>
                    <ha-icon class="track-button-icon" style="--mdc-icon-size: ${this.chore_icon_size}px;"
                             .icon=${this.chore_icon}></ha-icon>
                </mwc-icon-button>
            `
        }

        return html`
            <mwc-button
                    @click=${() => this._trackChore(item.id, item.name)}>
                ${this._translate("Track")}
            </mwc-button>
        `
    }

    _renderTrackTaskButton(item) {
        if (this.task_icon != null) {
            return html`
                <mwc-icon-button class="track-checkbox"
                                 .label=${this._translate("Track")} @click=${() => this._trackTask(item.id, item.name)}>
                    <ha-icon class="track-button-icon" style="--mdc-icon-size: ${this.task_icon_size}px;"
                             .icon=${this.task_icon}></ha-icon>
                </mwc-icon-button>
            `
        }

        return html`
            <mwc-button
                    @click=${() => this._trackTask(item.id, item.name)}>
                ${this._translate("Track")}
            </mwc-button>
        `
    }

    _calculateDaysTillNow(date) {
        const now = DateTime.now();
        return date.startOf('day').diff(now.startOf('day'), 'days').days;
    }

    _dueHtmlClass(dueInDays) {
        if (dueInDays == null) {
            return null;
        } else if (dueInDays < 0) {
            return "overdue";
        } else if (dueInDays < 1) {
            return "due-today";
        } else {
            return "not-due";
        }
    }

    _formatDueDate(dueDate, dueInDays) {
        if (dueInDays < 0) {
            return this._translate("Overdue");
        } else if (dueInDays < 1) {
            return this._translate("Today");
        } else if (dueInDays < 2) {
            return this._translate("Tomorrow");
        } else if (dueInDays < this.due_in_days_threshold) {
            return this._translate(`In ${dueInDays} days`);
        } else {
            return this._formatDate(dueDate, true);
        }
    }

    _formatLastTrackedDate(lastTrackedDate, lastTrackedDays, dateOnly) {
        if (lastTrackedDays < 1) {
            return this._translate("Today");
        } else if (lastTrackedDays < 2) {
            return this._translate("Yesterday");
        } else if (lastTrackedDays < this.last_tracked_days_threshold) {
            return this._translate(`${lastTrackedDays} days ago`);
        } else {
            return this._formatDate(lastTrackedDate, dateOnly);
        }
    }

    _translate(string) {
        if ((this.config.custom_translation != null) && (this.config.custom_translation[string] != null)) {
            return this.config.custom_translation[string];
        }
        return string;
    }

    _taskDueDateInputFormat() {
        const now = DateTime.now();
        return now.toFormat("yyyy-LL-dd");
    }

    _formatDate(dateTime, isDateOnly = false) {
        if (dateTime == null) {
            return null;
        }

        let dateOptions;
        let timeOptions = {};
        if (this.config.use_long_date) {
            dateOptions = {month: 'long', day: 'numeric', year: 'numeric'};
        } else {
            dateOptions = {month: 'numeric', day: 'numeric', year: 'numeric'};
        }

        if (!isDateOnly) {
            timeOptions = {hour: 'numeric', minute: 'numeric', hour12: !this.config.use_24_hours};
        }

        const dateTimeFormatOptions = {...dateOptions, ...timeOptions};
        return dateTime.toLocaleString(dateTimeFormatOptions);
    }

    _toDateTime(date) {
        return DateTime.fromISO(date);
    }

    _isItemVisible(item) {
        let visible = false;
        
        visible = visible || (item.__due_in_days == null);
        visible = visible && (item.__type === "chore" ? this.show_chores_without_due : true);
        visible = visible && (item.__type === "task" ? this.show_tasks_without_due : true);

        visible = visible || (item.__due_in_days < 0);
        visible = visible || (item.__due_in_days <= this.show_days);

        visible = visible && (this.filter !== undefined ? this._checkMatchNameFilter(item) : true);
        visible = visible && (this.filter_user !== undefined ? this._checkMatchUserFilter(item) : true);

        return visible;
    }

    _checkMatchNameFilter(item) {
        if (Array.isArray(this.filter)) {
            return this.filter.some(e => item.name.includes(e)); // Item name matches any filter value
        }

        if (!item.name.includes(this.filter)) {
            return false;
        }

        if (this.remove_filter) {
            item.__filtered_name = item.name.replace(this.filter, "");
        }

        return true;
    }

    _checkMatchUserFilter(item) {
        return item.__user_id && item.__user_id === this.filter_user;
    }

    _getTasks(entity) {
        if (entity.attributes.tasks === undefined) {
            return null;
        }

        let items = JSON.parse(JSON.stringify(entity.attributes.tasks));
        if (items === undefined) {
            return null;
        }

        const tasks = [];
        items.map(item => {
            item.__type = "task";
            item.__user_id = item.assigned_to_user_id;
            if (item.due_date != null) {
                item.__due_date = this._toDateTime(item.due_date);
                item.__due_in_days = this._calculateDaysTillNow(item.__due_date);
            }

            if (this._isItemVisible(item)) {
                tasks.push(item);
            }
        });

        return tasks;
    }

    _getChores(entity) {
        if (entity.attributes.chores === undefined) {
            return null;
        }

        let items = JSON.parse(JSON.stringify(entity.attributes.chores));
        if (items === undefined) {
            return null;
        }

        const chores = [];
        items.map(item => {
            item.__type = "chore";
            if (item.next_execution_assigned_user) {
                item.__user_id = item.next_execution_assigned_user.id;
            }

            if (item.next_estimated_execution_time != null && item.next_estimated_execution_time.slice(0, 4) !== 2999) {
                item.__due_date = this._toDateTime(item.next_estimated_execution_time);
                item.__due_in_days = this._calculateDaysTillNow(item.__due_date);
            }

            if (item.last_tracked_time) {
                item.__last_tracked_date = this._toDateTime(item.last_tracked_time);
                item.__last_tracked_days = Math.abs(this._calculateDaysTillNow(item.__last_tracked_date));
            }

            if (this._isItemVisible(item)) {
                chores.push(item);
            }
        });

        return chores;
    }

    _trackChore(choreId, choreName) {
        // Hide the chore on the next render, for better visual feedback
        this.local_cached_hidden_items.push(`chore${choreId}`);
        this.requestUpdate();
        this._hass.callService("grocy", "execute_chore", {
            chore_id: choreId, done_by: this.userId
        });
        this._showTrackedToast(choreName);
    }

    _trackTask(taskId, taskName) {
        // Hide the task on the next render, for better visual feedback
        this.local_cached_hidden_items.push(`task${taskId}`);
        this.requestUpdate();
        this._hass.callService("grocy", "complete_task", {
            task_id: taskId
        });
        this._showTrackedToast(taskName);
    }

    _showTrackedToast(itemName) {
        this._showToast(itemName, this._translate("Tracked"));
    }

    _showAddedToast(itemName) {
        this._showToast(itemName, this._translate("Added"));
    }

    _showToast(itemName, action) {
        if (this.config.browser_mod) {
            this._hass.callService("browser_mod", "notification", {
                message: `${this._translate(action)} "${itemName}".`, duration: 3000
            });
        }
        this._fireHaptic();
    }
    
    _fireHaptic() {
        if (this.haptic != null) {
            const myevent = new Event("haptic", {bubbles: true, composed: true, cancelable: false});
            myevent.detail = this.haptic;
            window.dispatchEvent(myevent);
        }
    }

    _toggleOverflow(documentFragment) {
        let element;
        const elementsHidden = documentFragment.querySelectorAll('.hidden-class');
        const elementsShown = documentFragment.querySelectorAll('.show-class');

        for (element in elementsHidden) {
            if (elementsHidden.hasOwnProperty(element)) {
                elementsHidden[element].classList.remove("hidden-class");
                elementsHidden[element].classList.add("show-class");
            }
        }
        for (element in elementsShown) {
            if (elementsShown.hasOwnProperty(element)) {
                elementsShown[element].classList.remove("show-class");
                elementsShown[element].classList.add("hidden-class");
            }
        }
    }

    _toggleAddTask() {
        const x = this.shadowRoot.getElementById("add-task-row");
        const icon = this.shadowRoot.getElementById("add-task-icon");
        if (x.style.display === "none") {
            x.style.display = "flex";
            icon.icon = "mdi:chevron-up";
        } else {
            x.style.display = "none";
            icon.icon = "mdi:chevron-down";
        }
    }

    _addTask() {
        const taskName = this.shadowRoot.getElementById('add-task').value;
        const taskDueDate = this.shadowRoot.getElementById('add-date').value;
        let taskData = {};
        if (!taskName) {
            alert(this._translate("'Name' can't be empty"));
            return;
        }

        taskData["name"] = taskName;
        if (taskDueDate) {
            let parsedDate = DateTime.fromFormat(taskDueDate, "yyyy-LL-dd");
            if (!parsedDate.isValid) {
                alert(this._translate("Due date must be empty or a valid date in format yyyy-mm-dd"));
                return;
            }

            taskData["due_date"] = taskDueDate;
        }

        taskData["assigned_to_user_id"] = this.userId;

        this._hass.callService("grocy", "add_generic", {
            entity_type: "tasks", data: taskData
        });

        this.shadowRoot.getElementById('add-task').value = "";

        this._showAddedToast(taskName);
    }

    _configSetup() {
        this.userId = this.config.user_id ?? 1;
        this.filter = this.config.filter;
        this.filter_user = this.config.filter_user;
        this.remove_filter = this.config.remove_filter ?? false;
        this.show_quantity = this.config.show_quantity || null;
        this.show_days = this.config.show_days ?? null;
        this.show_chores_without_due = this.config.show_chores_without_due ?? true;
        this.show_tasks_without_due = this.config.show_tasks_without_due ?? true;
        this.show_assigned = this.config.show_assigned ?? true;
        this.show_track_button = this.config.show_track_button ?? true;
        this.show_last_tracked = this.config.show_last_tracked ?? true;
        this.show_last_tracked_by = this.config.show_last_tracked_by ?? true;
        this.filter_category = this.config.filter_category ?? null;
        this.show_category = this.config.show_category ?? true;
        this.show_description = this.config.show_description ?? true;
        this.show_empty = this.config.show_empty ?? true;
        this.show_create_task = this.config.show_create_task ?? false;
        this.show_overflow = this.config.show_overflow || false;
        this.chore_icon_size = this.config.chore_icon_size || 32;
        this.task_icon_size = this.config.task_icon_size || 24;
        this.expand_icon_size = this.config.expand_icon_size || 30;
        this.show_divider = this.config.show_divider ?? false;
        this.due_in_days_threshold = this.config.due_in_days_threshold || 0;
        this.last_tracked_days_threshold = this.config.last_tracked_days_threshold || 0;
        this.hide_text_with_no_data = this.config.hide_text_with_no_data ?? false;
        this.use_long_date = this.config.use_long_date ?? false;
        this.use_24_hours = this.config.use_24_hours ?? true;
        this.haptic = this.config.haptic ?? "selection";
        this.task_icon = null
        this.chore_icon = null
        this.use_icons = this.config.use_icons ?? false;
        if (this.use_icons) {
            this.task_icon = this.config.task_icon || 'mdi:checkbox-blank-outline';
            this.chore_icon = this.config.chore_icon || 'mdi:check-circle-outline';
        }
    }


    constructor() {
        super();
        this.local_cached_hidden_items = []
    }

    // @TODO: This requires more intelligent logic
    getCardSize() {
        return 3;
    }
}

// Configure the preview in the Lovelace card picker
window.customCards = window.customCards || [];
window.customCards.push({
    type: 'grocy-chores-card',
    name: 'Grocy Chores and Tasks Card',
    preview: false,
    description: 'A card used to display chores and/or tasks from the Grocy custom component.',
});

customElements.define('grocy-chores-card', GrocyChoresCard);
