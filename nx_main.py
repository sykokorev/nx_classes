# -*- coding: utf-8 -*-

import os
import csv
import logging


from nx_class import NX
from common_class import CommonClass


def create_assembly(root_dir, gte_dir):

    """
    Main function for creating NX assembly of flow path compressor and turbine
    :param root_dir: Directory in which file will be saved
    :param gte_dir: Directory with compressor/turbine data
    :return: None
    """

    coef = 1000 # Transfer to mm


    # Logging
    log_file = os.path.join(root_dir, 'nx_logging.log')
    formatter = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(
        filename=log_file,
        level=logging.WARNING,
        format=formatter
    )
    logger = logging.getLogger(__name__)

    airfoils_dir = os.path.join(root_dir, gte_dir, 'airfoils')
    files = CommonClass()

    file_exists, airfoil_files = files.get_files(airfoils_dir, ('.dat',))
    nx = NX()
    prt_dir = os.path.join(root_dir, gte_dir, 'prt')
    is_created, create_dir_msg = files.create_dir(prt_dir)

    # Create blade with airfoil points
    if is_created:
        if file_exists:
            for file_ in airfoil_files:
                airfoil = {}
                with open(file_, newline='') as csv_file:
                    i = 1
                    data = csv.reader(csv_file)

                    # Set coordinates dictionary
                    for row in data:
                        if f'section{i}' in row[0].split():
                            key = row[0]
                            airfoil[key] = []
                            i += 1
                        else:
                            airfoil[key].append([float(coord) for coord in row])

                guide_lines_points = [
                    [airfoil[k][10] for k in list(airfoil.keys())],
                    [airfoil[k][int(len(airfoil[k]) / 2 - 10)] for k in list(airfoil.keys())],
                    [airfoil[k][int(len(airfoil[k]) / 2 + 10)] for k in list(airfoil.keys())]
                ]

                nx_file_name = f'{os.path.splitext(os.path.split(file_)[1])[0]}.prt'
                nx_file_name = os.path.join(prt_dir, nx_file_name)

                file_parameters = {'file_name': nx_file_name}
                is_new_file_created, log_new_file= nx.create_new_nx_file(**file_parameters)

                spline_tags = {}
                guide_tags = {}

                if is_new_file_created:
                    # Create section curves
                    for key, val in airfoil.items():
                        curve_parameters = {
                            'points': val,
                            'degree': 2,
                            'coeff': 1000,
                            'closed_spline': True,
                            'spline_type': 'ThroughPoints',
                            'matched_knot': True,
                            'name': key
                        }
                        spline_tag, log_spline = nx.create_spline_with_points(**curve_parameters)
                        if spline_tag:
                            spline_tags[key] = spline_tag
                            logger.info(log_spline)
                        else:
                            logger.warning(f'{log_spline}. Section {key}')

                    # Create guide curves for swept method
                    for i, point in enumerate(guide_lines_points):
                        # Create guide lines
                        guide_curve_parameters = {
                            'points': point,
                            'degree': 2,
                            'coeff': 1000,
                            'closed_spline': False,
                            'spline_type': 'ThroughPoints',
                            'matched_knot': True,
                            'name': f'guide_spline_{i}'
                        }
                        guide_tag, log_guide_spline = nx.create_spline_with_points(**guide_curve_parameters)
                        if guide_tag:
                            guide_tags[i] = guide_tag
                            logger.info(f'{log_guide_spline}. Guide spline {i}')
                        else:
                            logger.warning(f'{log_guide_spline}. Guide spline {i}')

                    parameters_through_curves = {
                        'sections': spline_tags,
                        'help_points': [point[0] for point in airfoil.values()],
                        'surface_type': 'through_curves'
                    }

                    section_help_points = [[p * coef for p in point[0]] for point in airfoil.values()]
                    guide_help_points = [[p * coef for p in point[0]] for point in guide_lines_points]

                    parameters_swept = {
                        'sections': spline_tags,
                        'guides': guide_tags,
                        'section_help_points': section_help_points,
                        'guide_help_points': guide_help_points
                    }

                    tagged_swept_object, log_swept = nx.swept(**parameters_swept)

                    if tagged_swept_object:
                        logger.info(f'{log_swept}')
                    else:
                        logger.warning(f'{log_swept}')

                else:
                    logger.warning(log_new_file)
                is_new_file_closed, log_message = nx.close_all(nx_file_name)
                if is_new_file_closed:
                    logger.info(log_message)
                else:
                    logger.error(log_message)
    else:
        logger.critical(create_dir_msg)

    # Delete NX() object and create new NX() object
    del nx
    nx = NX()

    assembly_file = os.path.join(root_dir, 'assembly.prt')
    file_exists, prt_files_root_dir = files.get_files(root_dir, ('.prt',))
    # If assembly_file exists, set new file name
    if file_exists and assembly_file in prt_files_root_dir:
        logger.warning(f"File {assembly_file} exists")
        assembly_file = files.new_file_name(assembly_file)
        logger.warning(f"New assembly file name is {assembly_file}")

    # Create new assembly
    is_success, assembly_msg = nx.create_new_nx_file(file_name=assembly_file)
    print(is_success, assembly_msg)

    if is_success:
        file_exists, prt_files = files.get_files(prt_dir, ('.prt',))
        if file_exists:
            for part in prt_files:
                is_part_added, log_msg = nx.add_part_to_assembly(part, assembly_file)
                if not is_part_added:
                    logger.error(log_msg)

        # Adding curves to the assembly
        curves_files_dir = os.path.join(root_dir, 'curves')
        curves_exists, curves_files = files.get_files(curves_files_dir, ('.dat',))
        if curves_exists:
            for curve in curves_files:
                is_data_obtained, curve_points = files.get_data_from_file(curve)

                if is_data_obtained:
                    is_spline_added, spline_msg = nx.create_spline_with_points(
                        curve_points=curve_points, coeff=coef, closed_spline=False
                    )
                    if not is_spline_added:
                        logger.error(spline_msg)

        # Trying to save and close the assembly file
        is_new_file_closed, file_closes_msg = nx.close_all(assembly_file)
        if is_new_file_closed:
            logger.info(file_closes_msg)
        else:
            logger.error(file_closes_msg)
    else:
        logger.error(assembly_msg)


if __name__ == "__main__":

    root_dir = r"P:\sea_gte\assembly"
    gte_dir = os.path.join(root_dir, 'turbine')
    create_assembly(root_dir, gte_dir)
