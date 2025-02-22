#!/usr/bin/env python3
#
# ----------------------------------------------------------------------------
# "THE BEER-WARE LICENSE" (Revision 42):
# <phk@FreeBSD.org> wrote this file.  As long as you retain this notice you
# can do whatever you want with this stuff. If we meet some day, and you think
# this stuff is worth it, you can buy me a beer in return.   Poul-Henning Kamp
# ----------------------------------------------------------------------------
#
# This file produces a .SVG table of the HP1345A character rom

# pylint: skip-file

import io
from io import TextIOWrapper
from font.hp1345Font import Font


def polylines(
	svg: TextIOWrapper,
	indent: int,
	font: Font,
	ch: int,
	x=0,
	y=0,
	fontColour: str = "#000000",
	fontThickness: float = 0.8,
	shadow: str | None = None,
) -> tuple[int, int]:
	if shadow is not None:
		x0, y0 = (x, y)
		for i in font.vectors(ch):
			(dx, dy) = i[0]
			svg.write((" " * indent) + '<polyline points="')
			svg.write(f" {x},{y}")
			svg.write(f" {x + dx},{y + dy}")
			svg.write(f'" {shadow} />\n')
			for dx, dy in i:
				x += dx
				y += dy
		x, y = (x0, y0)

	for i in font.vectors(ch):
		if len(i) == 1:
			(dx, dy) = i[0]
			x += dx
			y += dy
		else:
			svg.write((" " * indent) + '<polyline points="')
			for dx, dy in i:
				x += dx
				y += dy
				svg.write(f" {x},{y}")
			svg.write('" />\n')

			# workaround for QTBUG-132468
			# all points are same if everything after first is 0
			allSame = True
			for dx, dy in i[1:]:
				if dx != 0 or dy != 0:
					allSame = False
					break
			if allSame:
				svg.write(
					(" " * indent)
					+ f"<circle cx='{x}' cy='{y}' r='{fontThickness / 2}' fill='{fontColour}' />\n"
				)
	return x, y


def createGrid(
	svg: TextIOWrapper, ind: int, x0: int, y0: int, x1: int, y1: int, markers: list[tuple[int, str]]
):
	# Make a list of grid lines and sort them by marker
	# to avoid lighter lines overlapping darker lines.

	lines: list[tuple[int, str, int, int, int, int]] = []
	for x in range(x0, x1 + 1):
		m = ""
		for a, b in markers:
			if x % a == 0:
				m = b
		lines.append((a, m, x, y0, x, y1))
	for y in range(y0, y1 + 1):
		m = ""
		for a, b in markers:
			if y % a == 0:
				m = b
		lines.append((a, m, x0, y, x1, y))

	lines.sort()
	writePolylines(svg, ind, lines)


def writePolylines(svg: TextIOWrapper, ind: int, lines: list[tuple[int, str, int, int, int, int]]):
	for _, b, x0, y0, x1, y1 in lines:
		svg.write(f'{" " * ind}<polyline points="{x0},{y0} {x1},{y1}" {b} />\n')


def makeTextGroup(
	font: Font,
	textBytes: bytes,
	scale=2.0,
	xOffset=0,
	yOffset=0,
	border=10,
	fontThickness=0.8,
	fontColour="#000000",
) -> tuple[str, float, float]:
	ss = bytearray(textBytes)

	boundingBox = [0, 0, 0, 0]
	x1, y1 = 0, 0
	for char in ss:
		(boundingBox, x1, y1) = font.boundingBox(char, bbox=boundingBox, x=x1, y=y1)

	width = scale * (xOffset + 2 * border + boundingBox[2] - boundingBox[0])
	height = scale * (yOffset + 2 * border + boundingBox[3] - boundingBox[1])

	svg = io.StringIO()
	svg.write("	<g")
	svg.write(
		' transform="matrix(%d,0,0,%d,%d,%d)" '
		% (
			scale,
			-scale,
			scale * (border + xOffset - boundingBox[0]),
			scale * (border + yOffset + boundingBox[3]),
		)
	)
	svg.write(
		f''' stroke-width="{fontThickness}"
		stroke="{fontColour}"
		stroke-linecap="round"
		stroke-linejoin="round"
		fill="none"'''
	)
	svg.write(">\n")

	x, y = 0, 0

	for char in ss:
		x, y = polylines(
			svg, 6, font, char, fontColour=fontColour, fontThickness=fontThickness, x=x, y=y
		)
		if chr(char) == "\r":
			x = 0
	svg.write("	</g>\n")
	return (svg.getvalue(), width, height)


def makeSvgString(
	font: Font,
	textBytes: bytes,
	scale=2,
	offset=0,
	border=10,
	addGrid=False,
	drawShadow=False,
	fontThickness=0.8,
	fontColour="#000000",
) -> tuple[str, int, int]:
	ss = bytearray(textBytes)

	boundingBox = [0, 0, 0, 0]
	x1, y1 = 0, 0
	for char in ss:
		(boundingBox, x1, y1) = font.boundingBox(char, bbox=boundingBox, x=x1, y=y1)

	width = scale * (offset + 2 * border + boundingBox[2] - boundingBox[0])
	height = scale * (offset + 2 * border + boundingBox[3] - boundingBox[1])

	svg = io.StringIO()
	svg.write('<?xml version="1.0" standalone="no"?>\n')
	svg.write('<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN"\n')
	svg.write(' "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">\n')
	svg.write('<svg version="1.1"\n')
	svg.write(f' viewBox="0 0 {width} {height}"\n')
	svg.write(' xmlns="http://www.w3.org/2000/svg">\n')
	svg.write('  <g stroke-linecap="round" stroke-linejoin="round" ')
	svg.write('fill="none"')
	svg.write(
		' transform="matrix(%d,0,0,%d,%d,%d)" '
		% (
			scale,
			-scale,
			scale * (border + offset - boundingBox[0]),
			scale * (border + offset + boundingBox[3]),
		)
	)
	svg.write(">\n")

	if addGrid:
		svg.write('	<g stroke-width=".2" stroke="#cccccc">\n')
		createGrid(
			svg,
			6,
			boundingBox[0] - border,
			boundingBox[1] - border,
			boundingBox[2] + border,
			boundingBox[3] + border,
			[(1, ""), (5, 'stroke="#aaaaaa"'), (10, 'stroke="#888888"')],
		)
		svg.write("	</g>\n")

	svg.write(f'	<g stroke-width="{fontThickness}" stroke="{fontColour}">\n')
	x, y = 0, 0

	shadow = 'stroke-width=".4" stroke="#99eeee"' if drawShadow else None

	for char in ss:
		x, y = polylines(
			svg,
			6,
			font,
			char,
			fontColour=fontColour,
			fontThickness=fontThickness,
			x=x,
			y=y,
			shadow=shadow,
		)
		if chr(char) == "\r":
			x = 0
	svg.write("	</g>\n")

	if drawShadow:
		svg.write('	<circle cx="0" cy="0" r=".7" fill="green" />\n')
		svg.write(f'	<circle cx="{x}" cy="{y}" r=".3" fill="red" />\n')

	svg.write("  </g>\n</svg>\n")
	return (svg.getvalue(), width, height)


def makeSvg(
	fileName: str,
	font: Font,
	textBytes: bytes,
	scale=10,
	offset=1,
	border=5,
	addGrid=True,
	drawShadow=True,
	fontThickness=0.8,
	fontColour="#000000",
):
	(svg, width, height) = makeSvgString(
		font,
		textBytes,
		scale=scale,
		offset=offset,
		border=border,
		addGrid=addGrid,
		drawShadow=drawShadow,
		fontThickness=fontThickness,
		fontColour=fontColour,
	)
	with open(fileName, "w", encoding="utf8") as f:
		f.write(svg)
	return (True, width, height)


def main():
	font = Font()
	makeSvg(
		"fig_wg.svg",
		font,
		"HP1345A\n\r(and WarGames)\r\ntesting more".encode("ascii"),
		scale=2,
		border=4,
		offset=0,
		addGrid=True,
		drawShadow=True,
		fontThickness=2,
		fontColour="#ff0000",
	)

	diffBetweenFonts()
	saveEachChar(font)
	saveCharsToTable(font)


def diffBetweenFonts():
	font = Font()
	font2 = Font("01347-80001.bin")
	font2.v[0x2E] = font.v[0x2C]
	makeSvg("fig_commas.svg", font2, ",.".encode("ascii"), border=5, offset=0)


def saveEachChar(font: Font):
	for char in range(256):
		v = font.vectors(char)
		if len(v) == 1:
			continue
		makeSvg(f"_wargames_{char:02x}.svg", font, bytes([char]), scale=10, border=5, offset=5)


def saveCharsToTable(font: Font):
	grid = 40
	width = 17 * grid
	height = 17 * grid
	svg = open("fig_table.svg", "w", encoding="utf8")
	svg.write('<?xml version="1.0" standalone="no"?>\n')
	svg.write('<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN"\n')
	svg.write(' "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">\n')
	svg.write('<svg version="1.1"\n')
	svg.write(f' width="{width + 1}" height="{height + 1}"\n')
	svg.write(' xmlns="http://www.w3.org/2000/svg"')
	svg.write(' xmlns:xlink="http://www.w3.org/1999/xlink"')
	svg.write(">\n")
	svg.write('  <g stroke-linecap="round" stroke-linejoin="round" ')
	svg.write('fill="none"')
	svg.write(f' transform="matrix(1,0,0,-1,0,{height - 1})" ')
	svg.write(">\n")

	svg.write('	<g stroke="#000000">\n')
	for i in range(16):
		b = bytearray("-%x".encode("ascii") % i)
		x = 5
		y = (15 - i) * grid + 10
		x, y = polylines(svg, 6, font, b[0], x=x, y=y)
		x, y = polylines(svg, 6, font, b[1], x=x, y=y)
		x = (i + 1) * grid + 5
		y = 16 * grid + 10
		x, y = polylines(svg, 6, font, b[1], x=x, y=y)
		x, y = polylines(svg, 6, font, b[0], x=x, y=y)
	svg.write("	</g>\n")

	def box(x: int, y: int, colour: str):
		svg.write(f'\t<rect x="{x}" y="{y}"')
		svg.write(f' width="{grid}" height="{grid}"')
		svg.write(f' style="fill:{colour};stroke:#999999"/>\n')

	for cx in range(16):
		for cy in range(16):
			x = (cx + 1) * grid
			y = cy * grid
			char = cx * 16 + (15 - cy)
			v = font.vectors(char)
			if len(v) == 0:
				box(x, y, "#eeeeee")
				continue
			(boundingBox, _, _) = font.boundingBox(char)
			boundingBox[0] -= 2
			boundingBox[1] -= 2
			boundingBox[2] += 2
			boundingBox[3] += 2
			svg.write(f'\t<a xlink:href="_wargames_{char:02x}.svg">\n')
			box(x, y, "#ffffff")
			svg.write('\t<g stroke="#000000"')
			scx = (grid - 0.0) / (boundingBox[2] - boundingBox[0])
			scy = (grid - 0.0) / (boundingBox[3] - boundingBox[1])
			sc = min(scx, scy, 1.8)
			svg.write(
				f' transform="matrix({sc:.2f},0,0,{sc:.2f},{x - sc * boundingBox[0]},'
				f'{y - sc * boundingBox[1]})" '
			)
			svg.write(" >\n")
			polylines(svg, 10, font, char)
			svg.write("\t</g>\n")
			svg.write("\t</a>\n")

	svg.write("  </g>\n")
	svg.write("</svg>\n")


if __name__ == "__main__":
	main()
