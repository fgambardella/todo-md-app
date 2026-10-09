"""Item-row widget construction for the todo_md GUI.

Everything arrives as parameters (items, images, colors, fonts, callbacks)
so this module never imports :mod:`todo_md.app`; tkinter is imported
lazily inside functions so the module stays importable on headless
machines.
"""

from __future__ import annotations


def bg_kwargs(bg: str | None, key: str = "bg") -> dict:
    """Return ``{key: bg}`` when ``bg`` is not None, else an empty dict.

    Plain tk widgets inherit an unset background from the system color,
    which does not follow the app palette; callers spread the result as
    keyword arguments to leave the background untouched on the native
    (``tk appappearance``) path and pin it on the clam fallback path.
    """
    return {key: bg} if bg is not None else {}


def build_item_row(
    parent,
    *,
    item,
    index,
    row_bg,
    active_fg,
    done_fg,
    base_font,
    trash_image,
    edit_image,
    on_toggle,
    on_delete,
    on_edit,
    on_double_click,
) -> tuple:
    """Build one packed item row and return its widgets.

    Creates a ``tk.Frame`` row (packed ``anchor="w"`` / ``fill=tk.X``)
    containing, in order: a checkbutton bound to ``on_toggle(index)``
    (packed left), a trash icon bound to ``on_delete(index)`` (packed
    right), an edit (pencil) icon bound to ``on_edit(index)`` (packed
    right, landing left of the trash icon), and the text label bound to
    ``on_double_click(index)`` (packed left, expanding; struck through
    and dimmed when done).

    Returns the 5-tuple ``(var, checkbutton, label, trash_label,
    edit_label)`` — the stored ``app._item_rows`` entries unpack by
    position in exactly that order.
    """
    import tkinter as tk

    row = tk.Frame(parent, **bg_kwargs(row_bg))
    row.pack(anchor="w", fill=tk.X)

    var = tk.IntVar(value=1 if item.done else 0)
    checkbutton = tk.Checkbutton(
        row,
        variable=var,
        command=lambda i=index: on_toggle(i),
        **bg_kwargs(row_bg),
    )
    checkbutton.pack(side=tk.LEFT, padx=(4, 6))

    # Edit (pencil) icon: packed after the trash icon, so with the
    # same side=RIGHT it lands strictly to its left.
    trash_label = tk.Label(row, image=trash_image, cursor="hand2", **bg_kwargs(row_bg))
    trash_label.pack(side=tk.RIGHT, padx=(6, 4))
    trash_label.bind("<Button-1>", lambda e, i=index: on_delete(i))

    edit_label = tk.Label(row, image=edit_image, cursor="hand2", **bg_kwargs(row_bg))
    edit_label.pack(side=tk.RIGHT, padx=(6, 0))
    edit_label.bind("<Button-1>", lambda e, i=index: on_edit(i))

    label_font = base_font.copy()
    if item.done:
        label_font.config(overstrike=1)
    else:
        label_font.config(overstrike=0)

    label = tk.Label(
        row,
        text=item.text,
        anchor="w",
        font=label_font,
        foreground=done_fg if item.done else active_fg,
        **bg_kwargs(row_bg),
    )
    label.pack(side=tk.LEFT, fill=tk.X, expand=True)
    label.bind("<Double-Button-1>", lambda _e, i=index: on_double_click(i))

    return var, checkbutton, label, trash_label, edit_label


def rebuild_rows(app) -> None:
    """Rebuild the rows of ``app.items_frame`` for ``app.current_list``.

    ``app`` is duck-typed (a ``TodoApp``) so this module never imports
    :mod:`todo_md.app`; tkinter and :func:`.theme.text_colors` are imported
    lazily so the module stays importable on headless machines.
    """
    from tkinter import font as tkfont
    from .models import visible_items
    from .theme import text_colors  # lazy: keep module importable headless

    if app.current_list is None:
        app.title_label.config(text="(no list selected)")
        return

    base_font = tkfont.nametofont("TkDefaultFont").copy()
    active_fg, done_fg = text_colors(app.root, app.items_frame)

    todo_list = app.controller.open_list(app.current_list)
    row_bg = app._palette["bg"] if app._palette is not None else None
    # Display order can differ from storage; equal duplicate items still
    # need their own original indices for toggle/delete callbacks.
    stored_indexes = {id(item): index for index, item in enumerate(todo_list.items)}
    for item in visible_items(todo_list.items, app.settings.completed_visible):
        index = stored_indexes[id(item)]
        app._item_rows.append(
            build_item_row(
                app.items_frame,
                item=item,
                index=index,
                row_bg=row_bg,
                active_fg=active_fg,
                done_fg=done_fg,
                base_font=base_font,
                trash_image=app._trash_image,
                edit_image=app._edit_image,
                on_toggle=app._on_toggle_item,
                on_delete=app._on_delete_item,
                on_edit=app._on_edit_item,
                on_double_click=app._on_item_double_click,
            )
        )
