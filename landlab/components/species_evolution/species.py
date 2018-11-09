"""Species SpeciesEvolver object.
"""
import numpy as np

from landlab.components.species_evolution import Zone


class Species(object):
    """The SpeciesEvolver base species.

    Species contains

    The identifier is a two element tuple automatically generated by
    SpeciesEvolver. The first element is the clade id designated by a letter or
    letters. The second element is the species number that is assigned
    sequentially for each clade. The clade id is passed to child species.
    """

    subtype = 'base'

    def __init__(self, initial_time, initial_zones, parent_species=None):
        """Initialize a species.

        Parameters
        ----------
        initial_time : float
            Initial time of the species.
        initial_zones : SpeciesEvolver Zone or Zone list
            A list of SpeciesEvolver Zone objects of the species at the initial
            time.
        parent_species : SpeciesEvolver Species
            The parent species object. The default value, 'None' indicates no
            parent species.
        """
        # Set parameters.
        self._identifier = None
        self.parent_species = parent_species

        # Set initial zone(s).
        if isinstance(initial_zones, list):
            z = initial_zones
        else:
            z = [initial_zones]
        self.zones = {initial_time: z}

    def __str__(self):
        return '<{} at {}>'.format(self.__class__.__name__, hex(id(self)))

    @classmethod
    def evolve_type(cls, prior_time, time, extant_species, zone_paths):
        origins = zone_paths.origin.tolist()

        # Get the species that persist in `time` given the outcome of the
        # macroevolution processes of the species.

        output = {'child_species': [], 'surviving_parent_species': []}

        for es in extant_species:
            # Get paths that include the zone origin of this species.
            species_zones = es.zones[prior_time]
            indices = np.where(np.isin(origins, species_zones))[0]

            if len(indices) > 0:
                es_paths = zone_paths.loc[indices]

                species_persists, child_species = es.evolve(time, es_paths)

                if species_persists:
                    output['surviving_parent_species'].append(es)

                if len(child_species) > 0:
                    output['child_species'].extend(child_species)

        return output

    def evolve(self, time, zone_paths, **kwargs):
        """Run species evolutionary processes.

        Extinction is not explicitly implemented in this method. The base class
        of species leaves extinction to the disappearance of the range of a
        species.

        Parameters
        ----------
        time : float

        zone_paths : Pandas DataFrame

        Returns
        -------
        output : dictionary
            Required keys:
                'species_persists' : boolean
                    `True` indicates that this species persists in `time`.
                    `False` indicates that this species is extinct by `time`.
                'child_species' : SpeciesEvolver Species list
                    The child species produced by the current species after the
                    macroevolution processes run. An empty array indicates no
                    child species.
            Optional keys:
                'species_evolver_add_on' : dictionary
                    The items of this dictionary will become items in the
                    SpeciesEvolver records for this time.
        """
        species_persists = True
        child_species = []

        # Disperse and speciate. Extinction effectively occurs when the species
        # does not disperse to or remain in any zones.

        for v in zone_paths.itertuples():
            if v.path_type in [Zone.ONE_TO_ONE, Zone.MANY_TO_ONE]:
                # The species in this zone disperses to/remains in the zone.
                self.zones[time] = v.destinations
                species_persists = True

            elif v.path_type in [Zone.ONE_TO_MANY, Zone.MANY_TO_MANY]:
                # The zone and the species within it was fragmented. A new
                # child species is added to every destination zone. The species
                # self does not continue. It is assumed to have evolved into
                # one of the child species.
                species_persists = False

                for d in v.destinations:
                    child_species_d = Species(time, d, parent_species=self)
                    child_species.append(child_species_d)

            elif v.path_type == Zone.ONE_TO_NONE:
                species_persists = False

        # Create a unique array of child species.
        child_species = np.array(list(set(child_species)))

        return species_persists, child_species

    @property
    def identifier(self):
        """Get the species identifier.

        Returns
        -------
        identifier : tuple
            The unique identifier of the species. The first element is the
            clade of a species represented by a string. The second element is
            the species number represented by an integer.
        """
        return self._identifier

    @property
    def clade(self):
        """Get the species clade identifier.

        Returns
        -------
        clade_identifier : string
            The string representation of the clade of the species.
        """
        return self._identifier[0]
