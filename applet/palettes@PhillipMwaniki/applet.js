const Applet = imports.ui.applet;
const PopupMenu = imports.ui.popupMenu;
const Settings = imports.ui.settings;
const Main = imports.ui.main;
const { St, Gio, GLib, Clutter } = imports.gi;

const UUID = 'palettes@PhillipMwaniki';

class PalettesApplet extends Applet.IconApplet {
    constructor(metadata, orientation, panelHeight, instanceId) {
        super(orientation, panelHeight, instanceId);
        this.set_applet_icon_symbolic_name('applications-graphics-symbolic');
        this.set_applet_tooltip('Palettes');

        this.settings = new Settings.AppletSettings(this, UUID, instanceId);
        this.settings.bind('hotkey', 'hotkey', () => this._bindKeys());
        this.settings.bind('next-hotkey', 'nextHotkey', () => this._bindKeys());
        this.settings.bind('cli', 'cli');

        this.menuManager = new PopupMenu.PopupMenuManager(this);
        this.menu = new Applet.AppletPopupMenu(this, orientation);
        this.menuManager.addMenu(this.menu);
        this.menu.connect('open-state-changed', (m, open) => { if (open) this._refresh(); });

        this._busy = false;
        this._bindKeys();
        this._refresh();
    }

    _cliPath() {
        return (this.cli || '~/.local/bin/palette').replace(/^~/, GLib.get_home_dir());
    }

    _run(args, onDone) {
        let proc;
        try {
            proc = Gio.Subprocess.new([this._cliPath(), ...args],
                Gio.SubprocessFlags.STDOUT_PIPE | Gio.SubprocessFlags.STDERR_PIPE);
        } catch (e) {
            global.logError(`${UUID}: ${e.message}`);
            onDone(false, '', e.message);
            return;
        }
        proc.communicate_utf8_async(null, null, (p, res) => {
            let ok = false, out = '', err = '';
            try {
                [, out, err] = p.communicate_utf8_finish(res);
                ok = p.get_successful();
            } catch (e) {
                err = e.message;
            }
            if (!ok) global.logError(`${UUID}: palette ${args.join(' ')} failed: ${err}`);
            onDone(ok, out, err);
        });
    }

    _refresh() {
        this._run(['json'], (ok, out) => {
            if (!ok) return;
            try {
                this._data = JSON.parse(out);
            } catch (e) {
                return;
            }
            this._buildMenu();
        });
    }

    _buildMenu() {
        this.menu.removeAll();
        const { current, palettes } = this._data;

        const header = new PopupMenu.PopupMenuItem('Palettes', { reactive: false });
        header.label.add_style_class_name('palettes-header');
        this.menu.addMenuItem(header);

        for (const p of palettes) {
            const item = new PopupMenu.PopupBaseMenuItem();
            const row = new St.BoxLayout({ style_class: 'palettes-row' });

            const swatch = new St.BoxLayout({
                style_class: 'palettes-swatch',
                style: `background-color: ${p.bg}; border: 1px solid ${p.outline};`,
            });
            for (const c of [p.accent, p.accent2, p.ansi[1], p.ansi[2], p.ansi[3], p.fg]) {
                swatch.add_child(new St.Bin({ style_class: 'palettes-dot', style: `background-color: ${c};` }));
            }
            row.add_child(swatch);

            const label = new St.Label({ text: p.name, y_align: Clutter.ActorAlign.CENTER, style_class: 'palettes-name' });
            row.add_child(label);
            row.add_child(new St.Icon({
                icon_name: 'object-select-symbolic',
                icon_size: 14,
                style_class: 'palettes-check',
                opacity: p.slug === current ? 255 : 0,
                y_align: Clutter.ActorAlign.CENTER,
            }));
            item.addActor(row, { expand: true });

            item.connect('activate', () => this._apply(['apply', p.slug], p.name));
            this.menu.addMenuItem(item);
        }

        this.menu.addMenuItem(new PopupMenu.PopupSeparatorMenuItem());
        const next = new PopupMenu.PopupIconMenuItem('Next palette', 'media-skip-forward-symbolic', St.IconType.SYMBOLIC);
        next.connect('activate', () => this._apply(['next'], 'next palette'));
        this.menu.addMenuItem(next);
        if (current) {
            const restore = new PopupMenu.PopupIconMenuItem('Restore original look', 'edit-undo-symbolic', St.IconType.SYMBOLIC);
            restore.connect('activate', () => this._apply(['restore'], 'original look'));
            this.menu.addMenuItem(restore);
        }
    }

    _apply(args, what) {
        if (this._busy) return;
        this._busy = true;
        this.set_applet_tooltip(`Applying ${what}…`);
        this.actor.add_style_pseudo_class('checked');
        this._run(args, (ok, out, err) => {
            this._busy = false;
            this.actor.remove_style_pseudo_class('checked');
            this.set_applet_tooltip('Palettes');
            if (!ok) Main.notifyError('Palettes', (err || 'palette command failed').trim().split('\n').pop());
            this._refresh();
        });
    }

    _bindKeys() {
        Main.keybindingManager.removeXletHotKey(this, 'open');
        Main.keybindingManager.removeXletHotKey(this, 'next');
        if (this.hotkey) Main.keybindingManager.addXletHotKey(this, 'open', this.hotkey, () => this.menu.toggle());
        if (this.nextHotkey) Main.keybindingManager.addXletHotKey(this, 'next', this.nextHotkey, () => this._apply(['next'], 'next palette'));
    }

    on_applet_clicked() {
        this.menu.toggle();
    }

    on_applet_removed_from_panel() {
        Main.keybindingManager.removeXletHotKey(this, 'open');
        Main.keybindingManager.removeXletHotKey(this, 'next');
        this.settings.finalize();
    }
}

function main(metadata, orientation, panelHeight, instanceId) {
    return new PalettesApplet(metadata, orientation, panelHeight, instanceId);
}
