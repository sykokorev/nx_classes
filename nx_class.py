# -*- coding: utf-8 -*-

import os
import NXOpen as Nx
import NXOpen.Features as Ftr

from NXOpen import SectionCollection as SecCol


def points_list_converted(points):
    """
    Converts list of curve points to match for
    a creating StudioSpline curve
    :param points: list
        List of curves points that has been obtained
        from dat file
    :return: list of coordinates corresponding to
        create_spline_from_points method of the NXAssembly class
    """

    coordinates = []
    for point in points:
        x = (-1) * point[1]
        y = 0
        z = point[0]
        coordinates.append([x, y, z])
    return coordinates


class NX:
    """
    A class provides methods to create Siemens NX objects

    Methods
    -------
    import_files(in_file=None, out_file=None, in_file_type='iges')
        Imports iges file and saves it to prt format
    create_prt_file(iges_file: str, prt_dir: str)
        Opens an iges file and saves it to the prt_dir folder
    close_all(prt_file: str)
        Saves and closes all modified files
    create_new_nx_file(**parameters)
        Creates new NX prt file with the set parameters
    add_part_to_assembly(part, assembly_file=None)
        Adds prt file to an assembly file
    create_spline_with_points(**parameters)
        Creates studio spline object with the set parameters
    through_curves(**parameters)
        Creates solid or sheet body passing through curves with the set parameters
    swept(**parameters)
        Creates solid or sheet body with swept method with the set parameters
    """

    def __init__(self):
        """
        Constructs necessary attributes for handling NX Objects

        :param self.session: A NX current session
        :param self.new_file: A NXOpen NewFile Class for handling
        new nx file
        """

        self.session = Nx.Session.GetSession()
        self.new_file = self.session.Parts.FileNew()

    def import_file(self, in_file=None, out_file=None, in_file_type='iges'):
        """
        Imports file iges format (or another type file) and saves it to prt format
        :param in_file: File that will be imported to new NX file (str)
        :param out_file: File in which in_file will be saved (str)
        :param in_file_type: Type of input file (str)
        :return: Logging message (str)
        """

        if in_file:
            if in_file_type == 'iges':
                iges_importer = self.session.DexManager.CreateIgesImporter()
                iges_importer.CopiousData = Nx.IgesImporter.CopiousDataEnum.LinearNURBSpline
                iges_importer.SmoothBSurf = True
                iges_importer.LayerDefault = 10
                iges_importer.InputFile = in_file
                iges_importer.OutputFile = out_file
                iges_importer.FileOpenFlag = False
                iges_importer.LayerMask = "0-99999"
                try:
                    iges_importer.Commit()
                    iges_importer.Destroy()
                    msg = f"Iges file {os.path.split(out_file)[1]} has " \
                          f"been successfully imported."
                    msg += f"\nOutput file {out_file}"
                    return msg
                except Nx.NXException as ex:
                    msg = f"Iges file {os.path.split(out_file)[1]} has not been imported."
                    msg += f"An error occurred: {str(ex)}."
                    return msg

    def create_prt_file(self, igs_file: str, prt_dir: str):

        """
        Create new NX prt file from an iges file
        :param igs_file: Input iges file (str)
        :param prt_dir: Full directory name in which prt file will be saved
        :return: Bool, str
            True if file has been created or False otherwise and logging message
        """

        prt_file = os.path.splitext(os.path.split(igs_file)[1])[0] + '.prt'
        prt_file = os.path.join(prt_dir, prt_file)

        try:
            base_part, part_load_status = self.session.Parts.OpenBase(igs_file)
            part_load_status.Dispose()
        except Nx.NXException as ex:
            msg = f"Trying to open file '{igs_file}'. " + str(ex)
            return False, msg

        if part_load_status:
            try:
                part_save_status = base_part.SaveAs(prt_file)
                part_save_status.Dispose()
                msg = f"File '{prt_file}' has been successfully created."
                close_modified = Nx.BasePart.CloseModified.CloseModified
                self.session.Parts.CloseAll(close_modified, None)
                return True, msg
            except Nx.NXException as ex:
                msg = f"Trying to save '{os.path.split(prt_file)[1]}'. " + str(ex)
                return False, msg

    def close_all(self, prt_file):

        """
        Closes all parts of NX Work Part Object
        :param prt_file: File that will be closed
        :return: Bool, str
            True if file has been closed or False otherwise and logging message
        """

        whole_tree = Nx.BasePart.SaveComponents.TrueValue
        close_modified = Nx.BasePart.CloseAfterSave.FalseValue
        work_part = self.session.Parts.Work

        try:
            save_status = work_part.Save(whole_tree, close_modified)
            save_status.Dispose()
            self.session.Parts.CloseAll(Nx.BasePart.CloseModified.CloseModified, None)
            work_part = Nx.Part.Null
            msg = f"File {prt_file} has been successfully saved and closed."
            return True, msg
        except Nx.NXException as ex:
            msg = f"Trying to save and close file '{prt_file}'. An error occurred {str(ex)}."
            return False, msg

    def create_new_nx_file(self, **parameters):

        """
        Creates new NX file
        :param file_name: str
            Creating file name
        :param template: srt,
            Sets the name of the template part from which the new
            file being created
        :param app_name: str,
            Sets the application type for the new file being created
        :param tmp_presentation_name: str,
            Sets the presentation name of the underlying template
            which is used for the new file being created
        :return: Bool, str
            True if NewFile Class has been created successfully or False otherwise
            and logging message
        """

        file_name = parameters.get('file_name', None)
        template = parameters.get('template', 'model-plain-1-mm-template.prt')
        app_name = parameters.get('app_name', 'ModelTemplate')
        tmp_presentation_name = parameters.get('tmp_presentation_name', 'Model')

        if file_name:
            self.new_file.NewFileName = file_name
            self.new_file.TemplateFileName = template
            self.new_file.ApplicationName = app_name
            self.new_file.TemplatePresentationName = tmp_presentation_name

            self.new_file.UseBlankTemplate = False
            self.new_file.Units = Nx.Part.Units.Millimeters
            self.new_file.RelationType = ""
            self.new_file.TemplateType = Nx.FileNewTemplateType.Item
            self.new_file.ItemType = ""
            self.new_file.MasterFileName = ""

            self.new_file.SetCanCreateAltrep(False)

            try:
                nx_obj_file = self.new_file.Commit()
                file_name = os.path.split(file_name)[1]
                msg = f"File '{file_name}' has been successfully created."
                self.new_file.Destroy()
                return True, msg
            except Nx.NXException as ex:
                file_name = os.path.split(file_name)[1]
                msg = f"File '{file_name}' has not been created. An error occurred: {str(ex)}"
                return False, msg

    def add_part_to_assembly(self, part, assembly_file=None):

        """
        Creates ComponentBuilder Class for adding an assembly part and
        adds an assembly part to an assembly
        :param part: str,
            Full part file name which is being added
        :param assembly_file: str,
            Full assembly file name in which part is being added
        :return: False or Tagged Object and logging message
        """

        if assembly_file:
            self.session.ApplicationSwitchImmediate("UG_APP_MODELING")

            work_part = self.session.Parts.Work
            component_name = os.path.splitext(os.path.split(part)[1])[0]
            component_builder = work_part.AssemblyManager.CreateAddComponentBuilder()
            component_pos = work_part.ComponentAssembly.Positioner
            component_pos.ClearNetwork()
            component_pos.BeginAssemblyConstraints()
            allow_interpart_positioning = self.session.Preferences.Assemblies.InterpartPositioning
            component_network = component_pos.EstablishNetwork()
            component_network.MoveObjectsState = True
            component_builder.SetInitialLocationType(
                Nx.Assemblies.AddComponentBuilder.LocationType.WorkPartAbsolute
            )
            component_builder.SetComponentAnchor(
                Nx.Assemblies.ProductInterface.InterfaceObject.Null
            )
            component_builder.Layer = 10
            component_builder.ReferenceSet = "Use Model"
            component_builder.ComponentName = component_name

            base_part, part_load_status = self.session.Parts.Open(part)
            part_load_status.Dispose()

            part_to_use = [Nx.BasePart.Null] * 1
            part_to_use[0] = base_part
            component_builder.SetPartsToAdd(part_to_use)
            component_network.Solve()
            work_part.AssignPermanentName(assembly_file)

            try:
                nx_obj_builder = component_builder.Commit()
                obj_tag = nx_obj_builder.Tag
                component_builder.Destroy()
                component_pos.ClearNetwork()
                msg = f"Part {part} has been successfully added."
                return obj_tag, msg
            except Nx.NXException as ex:
                msg = f"Error committing component {part}. " + str(ex)
                return False, msg

    def create_spline_with_points(self, **parameters):

        """
        Creates StudioSplineBuilder for drawing a spline from points
        and draws Studio Spline
        :param curve_points: list,
            A list of curve points in format
            [[x0, y0, z0], [x1, y1, z1], ... [xn, yn, zn]]
        :param coeff: int,
            Units convert
        :param spline_degree: int,
            Degree of spline curve
        :param matched_knot: Bool,
            Placed knots only where you locate defining points
        :param spline_type: str,
            Can take two values ThroughPoints or ByPoles
        :param closed_spline: Bool,
            If spline has to be closed or not
        :return: False or Tagged object and logging message
        """

        curve_points = parameters.get('points', None)
        coeff = parameters.get('coeff', 1)
        spline_degree = parameters.get('degree', 3)
        matched_knot = parameters.get('matched_knot', True)
        spline_type = parameters.get('spline_type', 'ThroughPoints')
        closed_spline = parameters.get('closed_spline', True)
        name = parameters.get('name', False)

        if curve_points:
            work_part = self.session.Parts.Work
            studio_spline_builder = work_part.Features.CreateStudioSplineBuilderEx(Nx.NXObject.Null)

            if matched_knot:
                studio_spline_builder.MatchKnotsType = Ftr.StudioSplineBuilderEx.MatchKnotsTypes.Cubic
            else:
                studio_spline_builder.MatchKnotsType = Ftr.StudioSplineBuilderEx.MatchKnotsTypes.NotSet

            if spline_type == 'ThroughPoints':
                studio_spline_builder.Type = Ftr.StudioSplineBuilderEx.Types.ThroughPoints
            elif spline_type == 'ByPoles':
                studio_spline_builder.Type = Ftr.StudioSplineBuilderEx.Types.ByPoles
            else:
                studio_spline_builder.Type = Ftr.StudioSplineBuilderEx.Types.NotSet

            studio_spline_builder.Degree = spline_degree
            studio_spline_builder.IsPeriodic = closed_spline

            for point in curve_points:
                x, y, z = point[0], point[1], point[2]

                try:
                    x, y, z = float(x), float(y), float(z)
                    x *= coeff
                    y *= coeff
                    z *= coeff
                except ValueError:
                    msg = f"Coordinates value x: {x}, y: {y}, z: {z}. "
                    msg += "Data type mismatches."
                    return False, msg

                coordinates = Nx.Point3d(x, y, z)
                spline_point = work_part.Points.CreatePoint(coordinates)
                geometric_constraint_data = studio_spline_builder.ConstraintManager.CreateGeometricConstraintData()
                geometric_constraint_data.Point = spline_point
                studio_spline_builder.ConstraintManager.Append(geometric_constraint_data)
            try:
                nx_object = studio_spline_builder.Commit()
                obj_tag = nx_object.Tag
                studio_spline = nx_object
                if name:
                    studio_spline.SetName(name)
                else:
                    studio_spline.SetName('spline')

                studio_spline_builder.Destroy()
                msg = f"Studio spline has been successfully created."
                return obj_tag, msg
            except Nx.NXException as ex:
                msg = f"Studio spline has not been created. An error occurred {str(ex)}."
                return False, msg

    def through_curves(self, **parameters):

        """
        Create solid body or surfaces through  curves
        :param parameters: dict;
            :parameter: section_curves: curves tags dict
            :parameter: preserve_shape: bool allows to keep shape edges
            :parameter: help_points: list of helping points for the constraint
            :parameter: check_direction: bool is the directions of all sections should be checked
            :parameter: surface_type: str ThroughCurves object or StudioSurface object
                        need to be created
            :parameter: distance_tolerance: float=0.01 sets the distance tolerance
            :parameter: chaining_tolerance: float=0.0095 sets the chaining tolerance
            :parameter: angle_tolerance: float=0.5 sets the angle tolerance
        :return: False or Tagged Object and logging message.
        """

        section_curves = parameters.get('sections', {})
        preserve_shape = parameters.get('preserve_shape', False)
        help_points = parameters.get('help_points')
        check_directions = parameters.get('check_directions', True)
        surface_type = parameters.get('surface_type', 'through_curves')

        distance_tolerance = parameters.get('distance_tolerance', 0.01)
        chaining_tolerance = parameters.get('chaining_tolerance', 0.0095)
        angle_tolerance = parameters.get('angle_tolerance', 0.5)

        if section_curves:
            work_part = self.session.Parts.Work
            self.session.Preferences.Modeling.BodyType
            if surface_type == 'studio_surface':
                builder = work_part.Features.CreateStudioSurfaceBuilder(Ftr.Feature.Null)
                builder.AlignmentMethod.AlignCurve.DistanceTolerance = distance_tolerance
                builder.AlignmentMethod.AlignCurve.ChainingTolerance = chaining_tolerance
                builder.AlignmentMethod.AlignCurve.AngleTolerance = angle_tolerance
            elif surface_type == 'through_curves':
                builder = work_part.Features.CreateThroughCurvesBuilder(Ftr.Feature.Null)
                builder.PreserveShape = preserve_shape
                builder.PatchType = Nx.Features.ThroughCurvesBuilder.PatchTypes.Multiple
                builder.Alignment.AlignCurve.DistanceTolerance = distance_tolerance
                builder.Alignment.AlignCurve.ChainingTolerance = chaining_tolerance
                builder.Alignment.AlignCurve.AngleTolerance = angle_tolerance
            else:
                builder = work_part.Features.CreateStudioSurfaceBuilder(Ftr.Feature.Null)

            features = [Ftr.Feature.Null] * len(section_curves)
            sections = [Nx.Section.Null] * len(section_curves)

            # Set features
            for i, obj in enumerate(section_curves.values()):

                studio_spline = Nx.TaggedObjectManager.GetTaggedObject(obj)
                spline = studio_spline.GetEntities()[0]
                help_point = Nx.Point3d(*help_points[i])

                feature = [Ftr.Feature.Null] * 1
                feature[0] = studio_spline
                features[i] = spline
                rule = [work_part.ScRuleFactory.CreateRuleCurveFeature(feature)]

                section = work_part.Sections.CreateSection(
                    chaining_tolerance, distance_tolerance, angle_tolerance
                )
                section.AllowSelfIntersection(False)
                section.SetAllowedEntityTypes(Nx.Section.AllowTypes.OnlyCurves)
                section.AddToSection(
                    rule, spline, Nx.NXObject.Null, Nx.NXObject.Null,
                    help_point, Nx.Section.Mode.Create, False
                )
                direction = section.GetStartAndDirection()

                # Set same direction for all sections
                if check_directions:
                    if direction[2].X < 0:
                        section.ReverseDirection()

                if surface_type == 'studio_spline':
                    pass
                    # builder.SectionList.Append(section)
                else:
                    builder.SectionsList.Append(section)

                sections[i] = section

            if surface_type == 'studio_spline':
                builder.AlignmentMethod.SetSections(sections)
            else:
                builder.Alignment.SetSections(sections)

            try:
                nx_object = builder.CommitFeature()
                obj_tag = nx_object.Tag
                builder.Destroy()
                msg = 'Through curves object has been created successfully'
                return obj_tag, msg
            except Nx.NXException as ex:
                msg = 'Through curves object has not been created. An error occurred: {ex}'
                return False, msg

    def swept(self, **parameters):

        """
        Create solid body through swept method
        :param parameters: dict
            :parameter: section_curves: dict of tagged objects, studio splines of the sections curves
            :parameter: guide_curves: dict of tagged objects, studio splines of the guide curves
            :parameter: section_help_points: list of section help points for the constrain
            :parameter: guide_help_points: list of guide help points for the constrain
            :parameter: preserve_shape: bool allows to keep shape edges
            :parameter: distance tolerance: float=0.01 sets the distance tolerance
            :parameter: chaining_tolerance: float=0.0095 sets the chaining tolerance
            :parameter: g0_tolerance: float=0.01 sets the G0 (Position) tolerance
            :parameter: g1_tolerance: float=0.5 sets the G1 (Tangent) tolerance
        :return: False or Tagged Object and logging message
        """

        section_curves = parameters.get('sections', {})
        guide_curves = parameters.get('guides', {})
        section_help_points = parameters.get('section_help_points', None)
        guide_help_points = parameters.get('guide_help_points', None)
        preserve_shape = parameters.get('preserve_shape', False)

        distance_tolerance = parameters.get('distance_tolerance', 0.01)
        chaining_tolerance = parameters.get('chaining_tolerance', 0.0095)
        angle_tolerance = parameters.get('angle_tolerance', 0.5)
        g0_tolerance = parameters.get('g0', 0.01)
        g1_tolerance = parameters.get('g1', 0.5)

        if section_curves and guide_curves:
            work_part = self.session.Parts.Work
            self.session.Preferences.Modeling.BodyType

            # Create object of SweptBuilder class
            builder = work_part.Features.CreateSweptBuilder(Ftr.Swept.Null)
            builder.G0Tolerance = g0_tolerance
            builder.G1Tolerance = g1_tolerance
            builder.PreserveShapeOption = preserve_shape

            # Spine tolerances
            builder.Spine.DistanceTolerance = distance_tolerance
            builder.Spine.ChainingTolerance = chaining_tolerance
            builder.Spine.AngleTolerance = angle_tolerance

            builder.OrientationMethod.AngularLaw.AlongSpineData.Spine.DistanceTolerance = distance_tolerance
            builder.OrientationMethod.AngularLaw.AlongSpineData.Spine.ChainingTolerance = chaining_tolerance
            builder.OrientationMethod.AngularLaw.AlongSpineData.Spine.AngleTolerance = angle_tolerance

            builder.ScalingMethod.AreaLaw.AlongSpineData.Spine.DistanceTolerance = distance_tolerance
            builder.ScalingMethod.AreaLaw.AlongSpineData.Spine.ChainingTolerance = chaining_tolerance
            builder.ScalingMethod.AreaLaw.AlongSpineData.Spine.AngleTolerance = angle_tolerance

            builder.ScalingMethod.PerimeterLaw.AlongSpineData.Spine.DistanceTolerance = distance_tolerance
            builder.ScalingMethod.PerimeterLaw.AlongSpineData.Spine.ChainingTolerance = chaining_tolerance
            builder.ScalingMethod.PerimeterLaw.AlongSpineData.Spine.AngleTolerance = angle_tolerance

            # Section tolerances
            builder.AlignmentMethod.AlignCurve.DistanceTolerance = distance_tolerance
            builder.AlignmentMethod.AlignCurve.ChainingTolerance = chaining_tolerance
            builder.AlignmentMethod.AlignCurve.AngleTolerance = angle_tolerance

            builder.OrientationMethod.OrientationCurve.DistanceTolerance = distance_tolerance
            builder.OrientationMethod.OrientationCurve.ChainingTolerance = chaining_tolerance
            builder.OrientationMethod.OrientationCurve.AngleTolerance = angle_tolerance

            builder.OrientationMethod.AngularLaw.LawCurve.DistanceTolerance = distance_tolerance
            builder.OrientationMethod.AngularLaw.LawCurve.ChainingTolerance = chaining_tolerance
            builder.OrientationMethod.AngularLaw.LawCurve.AngleTolerance = angle_tolerance

            builder.ScalingMethod.AreaLaw.LawCurve.DistanceTolerance = distance_tolerance
            builder.ScalingMethod.AreaLaw.LawCurve.ChainingTolerance = chaining_tolerance
            builder.ScalingMethod.AreaLaw.LawCurve.AngleTolerance = angle_tolerance

            builder.ScalingMethod.ScalingCurve.DistanceTolerance = distance_tolerance
            builder.ScalingMethod.ScalingCurve.ChainingTolerance = chaining_tolerance
            builder.ScalingMethod.ScalingCurve.AngleTolerance = angle_tolerance

            builder.ScalingMethod.PerimeterLaw.LawCurve.DistanceTolerance = distance_tolerance
            builder.ScalingMethod.PerimeterLaw.LawCurve.ChainingTolerance = chaining_tolerance
            builder.ScalingMethod.PerimeterLaw.LawCurve.AngleTolerance = angle_tolerance

            # Create features, section and guide curves
            features = [Ftr.Feature.Null] * len(section_curves)
            sections = [Nx.Section.Null] * len(section_curves)
            guides_features = [Ftr.Feature.Null] * len(guide_curves)

            # Setting sections
            for i, obj in enumerate(section_curves.values()):
                studio_spline = Nx.TaggedObjectManager.GetTaggedObject(obj)
                spline = studio_spline.GetEntities()[0]
                help_point = Nx.Point3d(*section_help_points[i])
                feature = [Ftr.Feature.Null] * 1
                feature[0] = studio_spline
                features[i] = spline
                rule = [work_part.ScRuleFactory.CreateRuleCurveFeature(feature)]

                section = work_part.Sections.CreateSection(
                    chaining_tolerance, distance_tolerance, angle_tolerance
                )
                section.AllowSelfIntersection(True)
                section.SetAllowedEntityTypes(Nx.Section.AllowTypes.OnlyCurves)
                section.AddToSection(
                    rule, spline, Nx.NXObject.Null, Nx.NXObject.Null,
                    help_point, Nx.Section.Mode.Create, False
                )
                builder.SectionList.Append(section)
                sections[i] = section

            # Setting guide curves
            for i, obj in enumerate(guide_curves.values()):

                guide_spline = Nx.TaggedObjectManager.GetTaggedObject(obj)
                spline = guide_spline.GetEntities()[0]
                help_point = Nx.Point3d(*guide_help_points[i])
                feature = [Ftr.Feature.Null] * 1
                feature[0] = guide_spline
                guides_features[i] = spline
                rule = [work_part.ScRuleFactory.CreateRuleCurveFeature(feature)]

                section = work_part.Sections.CreateSection(
                    chaining_tolerance, distance_tolerance, angle_tolerance
                )
                builder.GuideList.Append(section)
                section.AllowSelfIntersection(True)
                section.SetAllowedEntityTypes(Nx.Section.AllowTypes.OnlyCurves)
                section.AddToSection(
                    rule, spline, Nx.NXObject.Null, Nx.NXObject.Null,
                    help_point, Nx.Section.Mode.Create, False
                )

                builder.ScalingMethod.AreaLaw.AlongSpineData.SetFeatureSpine(section)
                builder.ScalingMethod.PerimeterLaw.AlongSpineData.SetFeatureSpine(section)
                builder.OrientationMethod.AngularLaw.AlongSpineData.SetFeatureSpine(section)

            builder.ScalingMethod.ScalingOption = Nx.GeometricUtilities.ScalingMethodBuilder.ScalingOptions.Uniform
            builder.AlignmentMethod.SetSections(sections)

            try:
                nx_object = builder.Commit()
                obj_tag = nx_object.Tag
                nx_object.HideParents()
                msg = 'Swept object has been created successfully.'
                return obj_tag, msg
            except Nx.NXException as ex:
                msg = f'Swept object has not been created. An error occured {str(ex)}'
                return False, msg
